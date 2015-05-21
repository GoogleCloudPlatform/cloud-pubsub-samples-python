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


import argparse
import base64
import json
import re
import socket
import sys
import time

from apiclient import discovery

import httplib2

from oauth2client.client import GoogleCredentials


ARG_HELP = '''Available arguments are:
  PROJ list_topics
  PROJ create_topic TOPIC
  PROJ delete_topic TOPIC
  PROJ list_subscriptions
  PROJ list_subscriptions_in_topic TOPIC
  PROJ create_subscription SUBSCRIPTION LINKED_TOPIC [PUSH_ENDPOINT]
  PROJ delete_subscription SUBSCRIPTION
  PROJ connect_irc TOPIC SERVER CHANNEL
  PROJ publish_message TOPIC MESSAGE
  PROJ pull_messages SUBSCRIPTION
'''

PUBSUB_SCOPES = ["https://www.googleapis.com/auth/pubsub"]

ACTIONS = ['list_topics', 'list_subscriptions', 'list_subscriptions_in_topic',
           'create_topic', 'delete_topic', 'create_subscription',
           'delete_subscription', 'connect_irc', 'publish_message',
           'pull_messages']

BOTNAME = 'pubsub-irc-bot/1.0'

PORT = 6667

NUM_RETRIES = 3

BATCH_SIZE = 10


def help():
    """Shows a help message."""
    sys.stderr.write(ARG_HELP)


def fqrn(resource_type, project, resource):
    """Returns a fully qualified resource name for Cloud Pub/Sub."""
    return "projects/{}/{}/{}".format(project, resource_type, resource)


def get_full_topic_name(project, topic):
    """Returns a fully qualified topic name."""
    return fqrn('topics', project, topic)


def get_full_subscription_name(project, subscription):
    """Returns a fully qualified subscription name."""
    return fqrn('subscriptions', project, subscription)


def check_args_length(argv, min):
    """Checks the arguments length and exits when it's not long enough."""
    if len(argv) < min:
        help()
        sys.exit(1)


def list_topics(client, args):
    """Shows the list of current topics."""
    next_page_token = None
    while True:
        resp = client.projects().topics().list(
            project='projects/{}'.format(args[0]),
            pageToken=next_page_token).execute(num_retries=NUM_RETRIES)
        if 'topics' in resp:
            for topic in resp['topics']:
                print topic['name']
        next_page_token = resp.get('nextPageToken')
        if not next_page_token:
            break


def list_subscriptions(client, args):
    """Shows the list of current subscriptions."""
    next_page_token = None
    while True:
        resp = client.projects().subscriptions().list(
            project='projects/{}'.format(args[0]),
            pageToken=next_page_token).execute(num_retries=NUM_RETRIES)
        for subscription in resp['subscriptions']:
            print json.dumps(subscription, indent=1)
        next_page_token = resp.get('nextPageToken')
        if not next_page_token:
            break


def list_subscriptions_in_topic(client, args):
    """Shows the list of subscriptions attached to a given topic."""
    next_page_token = None
    while True:
        topic = get_full_topic_name(args[0], args[2])
        resp = client.projects().topics().subscriptions().list(
            topic=topic,
            pageToken=next_page_token).execute(num_retries=NUM_RETRIES)
        for subscription in resp['subscriptions']:
            print subscription
        next_page_token = resp.get('nextPageToken')
        if not next_page_token:
            break


def create_topic(client, args):
    """Creates a new topic."""
    check_args_length(args, 3)
    topic = client.projects().topics().create(
        name=get_full_topic_name(args[0], args[2]),
        body={}).execute(num_retries=NUM_RETRIES)
    print 'Topic {} was created.'.format(topic['name'])


def delete_topic(client, args):
    """Deletes a topic."""
    check_args_length(args, 3)
    topic = get_full_topic_name(args[0], args[2])
    client.projects().topics().delete(
        topic=topic).execute(num_retries=NUM_RETRIES)
    print 'Topic {} was deleted.'.format(topic)


def create_subscription(client, args):
    """Creates a new subscription to a given topic."""
    check_args_length(args, 4)
    name = get_full_subscription_name(args[0], args[2])
    if '/' in args[3]:
        topic_name = args[3]
    else:
        topic_name = get_full_topic_name(args[0], args[3])
    body = {'topic': topic_name}
    if len(args) == 5:
        # push_endpoint
        body['pushConfig'] = {'pushEndpoint': args[4]}
    subscription = client.projects().subscriptions().create(
        name=name, body=body).execute(num_retries=NUM_RETRIES)
    print 'Subscription {} was created.'.format(subscription['name'])


def delete_subscription(client, args):
    """Deletes a subscription."""
    check_args_length(args, 3)
    subscription = get_full_subscription_name(args[0], args[2])
    client.projects().subscriptions().delete(
        subscription=subscription).execute(num_retries=NUM_RETRIES)
    print 'Subscription {} was deleted.'.format(subscription)


def _check_connection(irc):
    """Checks a connection to an IRC channel."""
    readbuffer = ''
    while True:
        readbuffer = readbuffer + irc.recv(1024)
        temp = readbuffer.split('\n')
        readbuffer = temp.pop()
        for line in temp:
            if "004" in line:
                return
            elif "433" in line:
                sys.err.write('Nickname is already in use.')
                sys.exit(1)


def connect_irc(client, args):
    """Connects to an IRC channel and publishes messages."""
    check_args_length(args, 5)
    server = args[3]
    channel = args[4]
    topic = get_full_topic_name(args[0], args[2])
    nick = 'bot-{}'.format(args[0])
    irc = socket.socket()
    print 'Connecting to {}'.format(server)
    irc.connect((server, PORT))

    irc.send("NICK {}\r\n".format(nick))
    irc.send("USER {} 8 * : {}\r\n".format(nick, BOTNAME))
    readbuffer = ''
    _check_connection(irc)
    print 'Connected to {}.'.format(server)

    irc.send("JOIN {}\r\n".format(channel))
    priv_mark = "PRIVMSG {} :".format(channel)
    p = re.compile(
        r'\x0314\[\[\x0307(.*)\x0314\]\]\x03.*\x0302(http://[^\x03]*)\x03')
    while True:
        readbuffer = readbuffer + irc.recv(1024)
        temp = readbuffer.split('\n')
        readbuffer = temp.pop()
        for line in temp:
            line = line.rstrip()
            parts = line.split()
            if parts[0] == "PING":
                irc.send("PONG {}\r\n".format(parts[1]))
            else:
                i = line.find(priv_mark)
                if i == -1:
                    continue
                line = line[i + len(priv_mark):]
                m = p.match(line)
                if m:
                    line = "Title: {}, Diff: {}".format(m.group(1), m.group(2))
                body = {
                    'messages': [{'data': base64.b64encode(str(line))}]
                }
                client.projects().topics().publish(
                    topic=topic, body=body).execute(num_retries=NUM_RETRIES)


def publish_message(client, args):
    """Publish a message to a given topic."""
    check_args_length(args, 4)
    topic = get_full_topic_name(args[0], args[2])
    message = base64.b64encode(str(args[3]))
    body = {'messages': [{'data': message}]}
    resp = client.projects().topics().publish(
        topic=topic, body=body).execute(num_retries=NUM_RETRIES)
    print ('Published a message "{}" to a topic {}. The message_id was {}.'
           .format(args[3], topic, resp.get('messageIds')[0]))


def pull_messages(client, args):
    """Pulls messages from a given subscription."""
    check_args_length(args, 3)
    subscription = get_full_subscription_name(args[0], args[2])
    body = {
        'returnImmediately': False,
        'maxMessages': BATCH_SIZE
    }
    while True:
        try:
            resp = client.projects().subscriptions().pull(
                subscription=subscription, body=body).execute(
                    num_retries=NUM_RETRIES)
        except Exception:
            time.sleep(0.5)
            continue
        receivedMessages = resp.get('receivedMessages')
        if receivedMessages is not None:
            ack_ids = []
            for receivedMessage in receivedMessages:
                message = receivedMessage.get('message')
                if message:
                    print base64.b64decode(str(message.get('data')))
                    ack_ids.append(receivedMessage.get('ackId'))
            ack_body = {'ackIds': ack_ids}
            client.projects().subscriptions().acknowledge(
                subscription=subscription, body=ack_body).execute(
                    num_retries=NUM_RETRIES)


def main(argv):
    """Invokes a subcommand."""
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('args', nargs='*', help=ARG_HELP)

    credentials = GoogleCredentials.get_application_default()
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_SCOPES)
    http = httplib2.Http()
    credentials.authorize(http=http)

    client = discovery.build('pubsub', 'v1beta2', http=http)
    flags = argparser.parse_args(argv[1:])
    args = flags.args
    check_args_length(args, 2)

    if args[1] in ACTIONS:
        globals().get(args[1])(client, args)
    else:
        help()
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)
