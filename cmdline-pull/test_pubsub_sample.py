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


import contextlib
import os
import StringIO
import sys
import unittest
import uuid


from pubsub_sample import main


TEST_PROJECT_ID_ENV = 'TEST_PROJECT_ID'
DEFAULT_TEST_PROJECT_ID = "cloud-pubsub-sample-test"


@contextlib.contextmanager
def captured_output():
    """Capture output and redirect to sys."""
    new_out, new_err = StringIO.StringIO(), StringIO.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def get_project_id():
    """Return the project id to use in the tests."""
    return os.getenv(TEST_PROJECT_ID_ENV, DEFAULT_TEST_PROJECT_ID)


class PubsubSampleTestCase(unittest.TestCase):
    """A test case for the Pubsub sample.

    Define a test case that creates and lists topics and subscriptions.
    Also tests publishing and pulling messages
    """

    @classmethod
    def setUpClass(cls):
        """Create a new topic and subscription with a random name."""
        random_id = uuid.uuid4()
        cls.topic = 'topic-%s' % random_id
        cls.sub = 'sub-%s' % random_id
        main(['pubsub_sample.py', get_project_id(), 'create_topic',
              cls.topic])
        main(['pubsub_sample.py', get_project_id(), 'create_subscription',
              cls.sub, cls.topic])
        # The third message is to check the consistency between base64
        # variants used on the server side and the client side.
        cls.messages = ['message-1-%s' % uuid.uuid4(),
                        'message-2-%s' % uuid.uuid4(),
                        '=@~']

    @classmethod
    def tearDownClass(cls):
        """Delete resources used in the tests."""
        main(['pubsub_sample.py', get_project_id(), 'delete_topic', cls.topic])
        main(['pubsub_sample.py', get_project_id(), 'delete_subscription',
              cls.sub])

    def test_list_topics(self):
        """Test the list_topics action."""
        expected_topic = ('projects/%s/topics/%s'
                          % (get_project_id(), self.topic))
        with captured_output() as (out, _):
            main(['pubsub_sample.py', get_project_id(), 'list_topics'])
        output = out.getvalue().strip()
        self.assertTrue(expected_topic in output)

    def test_list_subscriptions(self):
        """Test the list_subscriptions action."""
        expected_sub = ('projects/%s/subscriptions/%s'
                        % (get_project_id(), self.sub))
        with captured_output() as (out, _):
            main(['pubsub_sample.py', get_project_id(), 'list_subscriptions'])
        output = out.getvalue().strip()
        self.assertTrue(expected_sub in output)

    def test_publish_message(self):
        """Try to publish a message and check the output for the  message."""
        for message in self.messages:
            with captured_output() as (out, _):
                main(['pubsub_sample.py', get_project_id(), 'publish_message',
                      self.topic, message])
                output = out.getvalue().strip()
            self.assertTrue(message in output)

    def test_pull_message(self):
        """Try to pull messages from a subscription."""
        with captured_output() as (out, _):
            main(['pubsub_sample.py', get_project_id(), 'pull_messages',
                  self.sub, '-n'])
            output = out.getvalue().strip()
        for message in self.messages:
            self.assertTrue(message in output)
