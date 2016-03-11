#!/usr/bin/env python
# Copyright 2016 Google Inc. All Rights Reserved.
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


"""Cloud Pub/Sub gRPC sample application."""

from __future__ import print_function


import logging
import sys

from google.pubsub.v1 import pubsub_pb2
from grpc.beta import implementations
from grpc.framework.interfaces.face.face import NetworkError

from oauth2client import client


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

PUBSUB_ENDPOINT = "pubsub.googleapis.com"
SSL_PORT = 443
OAUTH_SCOPE = "https://www.googleapis.com/auth/pubsub",
GOOGLE_CREDS = client.GoogleCredentials.get_application_default()
SCOPED_CREDS = GOOGLE_CREDS.create_scoped(OAUTH_SCOPE)
TIMEOUT = 30


def auth_func(scoped_creds=SCOPED_CREDS):
    """Returns a token obtained from Google Creds."""
    authn = scoped_creds.get_access_token().access_token
    return [('authorization', 'Bearer %s' % authn)]


def make_channel_creds(ssl_creds, auth_func=auth_func):
    """Returns a channel with credentials callback."""
    call_creds = implementations.metadata_call_credentials(
        lambda ctx, callback: callback(auth_func(), None))
    return implementations.composite_channel_credentials(ssl_creds, call_creds)


def create_pubsub_stub(host=PUBSUB_ENDPOINT, port=SSL_PORT):
    """Creates a secure pubsub channel."""
    ssl_creds = implementations.ssl_channel_credentials(None, None, None)
    channel_creds = make_channel_creds(ssl_creds, auth_func)
    channel = implementations.secure_channel(host, port, channel_creds)
    return pubsub_pb2.beta_create_Publisher_stub(channel)


def list_topics(stub, project):
    """Lists topics in the given project."""
    req = pubsub_pb2.ListTopicsRequest(project=project)
    try:
        resp = stub.ListTopics(req, TIMEOUT)
        for t in resp.topics:
            print("Topic is: {}".format(t.name))
    except NetworkError, e:
        logging.warning('Failed to list topics: {}'.format(e))
        sys.exit(1)


def usage():
    """Prints usage to the stderr."""
    print('{} project_id'.format(sys.argv[0]), file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        usage()
        exit(1)
    stub = create_pubsub_stub()
    list_topics(stub, 'projects/{}'.format(sys.argv[1]))


if __name__ == '__main__':
    main()
