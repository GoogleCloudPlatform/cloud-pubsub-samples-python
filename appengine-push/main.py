#!/usr/bin/env python
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Cloud Pub/Sub sample application."""


import base64
import json
import logging
import re
import urllib

from apiclient import errors
from google.appengine.api import memcache
from google.appengine.ext import ndb

import jinja2

import webapp2

import constants
import pubsub_utils


JINJA2 = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'),
                            extensions=['jinja2.ext.autoescape'],
                            variable_start_string='((',
                            variable_end_string='))',
                            autoescape=True)

MAX_ITEM = 20

MESSAGE_CACHE_KEY = 'messages_key'


class PubSubMessage(ndb.Model):
    """A model stores pubsub message and the time when it arrived."""
    message = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)


class InitHandler(webapp2.RequestHandler):
    """Initializes the Pub/Sub resources."""
    def __init__(self, request=None, response=None):
        """Calls the constructor of the super and does the local setup."""
        super(InitHandler, self).__init__(request, response)
        self.client = pubsub_utils.get_client()
        self._setup_topic()
        self._setup_subscription()

    def _setup_topic(self):
        """Creates a topic if it does not exist."""
        topic_name = pubsub_utils.get_full_topic_name()
        try:
            self.client.projects().topics().get(
                topic=topic_name).execute()
        except errors.HttpError as e:
            if e.resp.status == 404:
                self.client.projects().topics().create(
                    name=topic_name, body={}).execute()
            else:
                logging.exception(e)
                raise

    def _setup_subscription(self):
        """Creates a subscription if it does not exist."""
        subscription_name = pubsub_utils.get_full_subscription_name()
        try:
            self.client.projects().subscriptions().get(
                subscription=subscription_name).execute()
        except errors.HttpError as e:
            if e.resp.status == 404:
                body = {
                    'topic': pubsub_utils.get_full_topic_name(),
                    'pushConfig': {
                        'pushEndpoint': pubsub_utils.get_app_endpoint_url()
                    }
                }
                self.client.projects().subscriptions().create(
                    name=subscription_name, body=body).execute()
            else:
                logging.exception(e)
                raise

    def get(self):
        """Shows an HTML form."""
        template = JINJA2.get_template('pubsub.html')
        endpoint_url = re.sub('token=[^&]*', 'token=REDACTED',
                              pubsub_utils.get_app_endpoint_url())
        context = {
            'project': pubsub_utils.get_project_id(),
            'topic': pubsub_utils.get_app_topic_name(),
            'subscription': pubsub_utils.get_app_subscription_name(),
            'subscriptionEndpoint': endpoint_url
        }
        self.response.write(template.render(context))


class FetchMessages(webapp2.RequestHandler):
    """A handler returns messages."""
    def get(self):
        """Returns recent messages as a json."""
        messages = memcache.get(MESSAGE_CACHE_KEY)
        if not messages:
            messages = PubSubMessage.query().order(
                -PubSubMessage.created_at).fetch(MAX_ITEM)
            memcache.add(MESSAGE_CACHE_KEY, messages)
        self.response.headers['Content-Type'] = ('application/json;'
                                                 ' charset=UTF-8')
        self.response.write(
            json.dumps(
                [message.message for message in messages]))


class SendMessage(webapp2.RequestHandler):
    """A handler publishes the given message."""
    def post(self):
        """Publishes the message via the Pub/Sub API."""
        client = pubsub_utils.get_client()
        message = self.request.get('message')
        if message:
            topic_name = pubsub_utils.get_full_topic_name()
            body = {
                'messages': [{
                    'data': base64.b64encode(message.encode('utf-8'))
                }]
            }
            client.projects().topics().publish(
                topic=topic_name, body=body).execute()
        self.response.status = 204


class ReceiveMessage(webapp2.RequestHandler):
    """A handler for push subscription endpoint.."""
    def post(self):
        if constants.SUBSCRIPTION_UNIQUE_TOKEN != self.request.get('token'):
            self.response.status = 404
            return

        # Store the message in the datastore.
        logging.debug('Post body: {}'.format(self.request.body))
        message = json.loads(urllib.unquote(self.request.body).rstrip('='))
        message_body = base64.b64decode(str(message['message']['data']))
        pubsub_message = PubSubMessage(message=message_body)
        pubsub_message.put()

        # Invalidate the cache
        memcache.delete(MESSAGE_CACHE_KEY)
        self.response.status = 200


APPLICATION = webapp2.WSGIApplication(
    [
        ('/', InitHandler),
        ('/fetch_messages', FetchMessages),
        ('/send_message', SendMessage),
        ('/_ah/push-handlers/receive_message', ReceiveMessage),
    ], debug=True)
