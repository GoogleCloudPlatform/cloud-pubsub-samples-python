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


"""Utility module for this Pub/Sub sample."""

import os
import threading

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import modules

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials

import constants


APPLICATION_NAME = "google-cloud-pubsub-appengine-sample/1.0"

PUBSUB_SCOPES = ["https://www.googleapis.com/auth/pubsub"]


client_store = threading.local()


def is_devserver():
    """Check if the app is running on devserver or not."""
    return os.getenv('SERVER_SOFTWARE', '').startswith('Dev')


def get_client():
    """Creates Pub/Sub client and returns it."""
    if not hasattr(client_store, 'client'):
        client_store.client = get_client_from_credentials(
            GoogleCredentials.get_application_default())
    return client_store.client


def get_client_from_credentials(credentials):
    """Creates Pub/Sub client from a given credentials and returns it."""
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_SCOPES)

    http = httplib2.Http(memcache)
    credentials.authorize(http)

    return discovery.build('pubsub', 'v1', http=http)


def get_full_topic_name():
    return 'projects/{}/topics/{}'.format(
        get_project_id(), get_app_topic_name())


def get_full_subscription_name():
    return 'projects/{}/subscriptions/{}'.format(
        get_project_id(), get_app_subscription_name())


def get_app_topic_name():
    return 'topic-pubsub-api-appengine-sample-python'


def get_app_subscription_name():
    return 'subscription-python-{}'.format(get_project_id())


def get_app_endpoint_url():
    return 'https://{}-dot-{}.appspot.com/receive_message?token={}'.format(
        get_current_version(), get_project_id(),
        constants.SUBSCRIPTION_UNIQUE_TOKEN)


def get_project_id():
    return app_identity.get_application_id()


def get_current_version():
    return modules.get_current_version_name()
