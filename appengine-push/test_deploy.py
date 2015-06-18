#!/usr/bin/env python
# Copyright 2015 Google Inc. All Rights Reserved.
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


"""Test classes for the command line Cloud Pub/Sub sample."""

import os
import time
import unittest
import urllib
import uuid

import httplib2

TEST_GAE_HOST_ENV = 'TEST_GAE_HOST'
DEFAULT_TEST_GAE_HOST = "py-dot-cloud-pubsub-sample-test.appspot.com"
MAX_RETRY = 3
SLEEP_TIME = 1
GAE_HOST = os.getenv(TEST_GAE_HOST_ENV, DEFAULT_TEST_GAE_HOST)


def url_for(path):
    """Returns the URL of the endpoint for the given path."""
    return 'https://%s%s' % (GAE_HOST, path)


class IntegrationTestCase(unittest.TestCase):
    """A test case for the Pubsub App Engine sample."""

    def setUp(self):
        random_id = uuid.uuid4()
        # The first three character will be encoded as a string
        # containing '+', in order to test the consistency on which
        # base64 variant to use on the server side and the client side.
        self.message = '=@~message-%s' % random_id
        self.http = httplib2.Http()

    def test_get(self):
        """Test accessing the top page."""
        (resp, content) = self.http.request(url_for('/'), 'GET')
        # This ensures that our App Engine service account is working
        # correctly.
        self.assertEquals(200, resp.status)

    def fetch_messages(self):
        """Fetch messages"""
        (_, content) = self.http.request(url_for('/fetch_messages'), 'GET')
        return content

    def test_send_message(self):
        """Test submitting a message."""
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        params = urllib.urlencode({'message': self.message})
        (resp, content) = self.http.request(
            url_for('/send_message'), 'POST', body=params, headers=headers)
        self.assertEquals(204, resp.status)
        found = False
        for i in range(MAX_RETRY):
            time.sleep(SLEEP_TIME)
            content = self.fetch_messages()
            if self.message in content:
                found = True
                break
        self.assertTrue(found)
