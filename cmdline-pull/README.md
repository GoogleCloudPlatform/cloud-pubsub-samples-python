cloud-pubsub-samples-python
===========================

cmdline-pull
------------

This is a command line sample application using the Cloud Pub/Sub
API. You can do the following things with this command line tool:

1. List/Create/Delete topics/subscriptions
2. Connect to an IRC channel and publish IRC massages.
3. Pull messages from a subscription and print those messages.

= Prerequisites

- Install Python-2.7 and google-api-python-client. Here is the
  instruction with virtualenv and pip.

  $ virtualenv -p python2.7 --no-site-packages .
  $ source bin/activate
  $ pip install --upgrade google-api-python-client

= Register your application

1. If you don't have a project, go to [Google Developers Console][1]
   and create a new project.

2. Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

3. Go to "Credentials" and create a new Client ID by selecting
   "Installed application" and "Other". Then click the "Download JSON"
   button and save it as 'client_secrets.json' in the project top
   directory.

= Run the application

  $ python pubsub_sample.py

  This will give you a help message. Here is an example session with
  this command.

  # create a new topic "test" on MYPROJ
  $ python pubsub_sample.py MYPROJ create_topic test

  # list the current topics
  $ python pubsub_sample.py MYPROJ list_topics

  # create a new subscription "sub" on the "test" topic
  $ python pubsub_sample.py MYPROJ create_subscription sub test

  # connect to the Wikipedia recent change channel
  $ python pubsub_sample.py \
    MYPROJ \
    connect_irc \
    test \
    irc.wikimedia.org \
    "#en.wikipedia"

  # fetch messages from the subscription "sub"
  $ python pubsub_sample.py MYPROJ pull_messages sub

Enjoy!


[1]: https://console.developers.google.com/project
