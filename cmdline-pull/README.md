# cloud-pubsub-samples-python


## cmdline-pull

This is a command line sample application using the Cloud Pub/Sub
API. You can do the following things with this command line tool:

- List/Create/Delete topics/subscriptions
- Connect to an IRC channel and publish IRC massages.
- Pull messages from a subscription and print those messages.

## Prerequisites

- Install Python-2.7, google-api-python-client and pycrypto. Here are
  the instructions with virtualenv and pip.

```
$ virtualenv -p python2.7 --no-site-packages .
$ source bin/activate
$ pip install -r requirements.txt
```
## Register your application

- If you don't have a project, go to [Google Developers Console][1]
  and create a new project.

- Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

- Go to "Credentials" and create a new Service Account, then download
  a new P12 key and comvert it to pem format with the following
  command:

  $ openssl pkcs12 -in p12file -nodes -nocerts > pemfile

  Password is "notasecret"

- Set the following environment variables.

  - SERVICE_ACCOUNT_EMAIL: The e-mail address of your service account.
  - PRIVKEY_PATH: The path of your private pem key file.

## Run the application

```
$ python pubsub_sample.py
```

This will give you a help message. Here is an example session with
this command.

```
# create a new topic "test" on MYPROJ
$ python pubsub_sample.py MYPROJ create_topic test

# list the current topics
$ python pubsub_sample.py MYPROJ list_topics

# create a new subscription "sub" on the "test" topic
$ python pubsub_sample.py MYPROJ create_subscription sub test

# publish a message "hello" to the "test" topic
$ python pubsub_sample.py MYPROJ publish_message test hello

# connect to the Wikipedia recent change channel
$ python pubsub_sample.py \
  MYPROJ \
  connect_irc \
  test \
  irc.wikimedia.org \
  "#en.wikipedia"

# fetch messages from the subscription "sub"
$ python pubsub_sample.py MYPROJ pull_messages sub
```

Enjoy!

[1]: https://console.developers.google.com/project
