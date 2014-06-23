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

from apiclient import sample_tools


ARG_HELP = '''Available arguments are:
  PROJ list_topics
  PROJ create_topic TOPIC
  PROJ delete_topic TOPIC
  PROJ list_subscriptions
  PROJ create_subscription SUBSCRIPTION LINKED_TOPIC
  PROJ delete_subscription SUBSCRIPTION
  PROJ connect_irc TOPIC SERVER CHANNEL
  PROJ pull_messages SUBSCRIPTION
'''

PUBSUB_SCOPES = ["https://www.googleapis.com/auth/pubsub"]

ACTIONS = ['list_topics', 'list_subscriptions', 'create_topic', 'delete_topic',
           'create_subscription', 'delete_subscription', 'connect_irc',
           'pull_messages']

BOTNAME = 'pubsub-irc-bot/1.0'

PORT = 6667


def help():
    """Shows a help message."""
    sys.stderr.write(ARG_HELP)


def fqrn(resource_type, project, resource):
    """Returns a fully qualified resource name for Cloud Pub/Sub."""
    return "/{}/{}/{}".format(resource_type, project, resource)

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
        params = {
            'query':
                'cloud.googleapis.com/project in (/projects/{})'.format(args[0])
        }
        if next_page_token:
            params['pageToken'] = next_page_token
        resp = client.topics().list(**params).execute()
        for topic in resp['topic']:
            print topic['name']
        next_page_token = resp.get('nextPageToken')
        if not next_page_token:
            break


def list_subscriptions(client, args):
    """Shows the list of current subscriptions."""
    next_page_token = None
    while True:
        params = {
            'query':
                'cloud.googleapis.com/project in (/projects/{})'.format(args[0])
        }
        if next_page_token:
            params['pageToken'] = next_page_token
        resp = client.subscriptions().list(**params).execute()
        for subscription in resp['subscription']:
            print json.dumps(subscription, indent=1)
        next_page_token = resp.get('nextPageToken')
        if not next_page_token:
            break


def create_topic(client, args):
    """Creates a new topic."""
    check_args_length(args, 3)
    body = {'name': get_full_topic_name(args[0], args[2])}
    topic = client.topics().create(body=body).execute()
    print 'Topic {} was created.'.format(topic['name'])


def delete_topic(client, args):
    """Deletes a topic."""
    check_args_length(args, 3)
    topic = get_full_topic_name(args[0], args[2])
    client.topics().delete(topic=topic).execute()
    print 'Topic {} was deleted.'.format(topic)


def create_subscription(client, args):
    """Creates a new subscription to a given topic."""
    check_args_length(args, 4)
    body = {'name': get_full_subscription_name(args[0], args[2]),
            'topic': get_full_topic_name(args[0], args[3])}
    subscription = client.subscriptions().create(body=body).execute()
    print 'Subscription {} was created.'.format(subscription['name'])


def delete_subscription(client, args):
    """Deletes a subscription."""
    check_args_length(args, 3)
    subscription = get_full_subscription_name(args[0], args[2])
    client.subscriptions().delete(subscription=subscription).execute()
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
                    'topic': topic,
                    'message': {'data': base64.urlsafe_b64encode(str(line))}
                }
                client.topics().publish(body=body).execute()


def pull_messages(client, args):
    """Pulls messages from a given subscription."""
    check_args_length(args, 3)
    subscription = get_full_subscription_name(args[0], args[2])
    body = {'subscription': subscription, 'returnImmediately': False}
    while True:
        try:
            resp = client.subscriptions().pull(body=body).execute()
        except Exception as e:
            time.sleep(0.5)
        message = resp.get('pubsubEvent').get('message')
        if message:
            print base64.b64decode(str(message.get('data')), '_/')
            ack_id = resp.get('ackId')
            ack_body = {'subscription': subscription, 'ackId': [ack_id]}
            client.subscriptions().acknowledge(body=body).execute()


def main(argv):
    """Invokes a subcommand."""
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('args', nargs='*', help=ARG_HELP)
    client, flags = sample_tools.init(
        argv, 'pubsub', 'v1beta1', __doc__, __file__,
        scope=PUBSUB_SCOPES, parents=[argparser])
    args = flags.args
    check_args_length(args, 2)

    if args[1] in ACTIONS:
        globals().get(args[1])(client, args)
    else:
        help()
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)
