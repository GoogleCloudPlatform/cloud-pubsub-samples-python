# cloud-pubsub-samples-python

## appengine-push

Note: The push endpoints don't work with the App Engine's local
devserver. The push notifications will go to an HTTP URL on the App
Engine server even when you run this sample locally. So we recommend
you deploy and run the app on App Engine.
TODO(tmatsuo): Better implementation for devserver.

## Register your application

- Go to
  [Google Developers Console](https://console.developers.google.com/project)
  and create a new project. This will automatically enable an App
  Engine application with the same ID as the project.

- Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

- For local development also follow the instructions below.

  - Go to "Credentials" and create a new Service Account.

  - Select "Generate new JSON key", then download a new JSON file.

  - Set the following environment variable.

    GOOGLE_APPLICATION_CREDENTIALS: the file path to the downloaded JSON file.

## Prerequisites

- Install Python-2.7, pip-6.0.0 or higher and App Engine Python SDK.
  We recommend you install
  [Cloud SDK](https://developers.google.com/cloud/sdk/) rather than
  just installing App Engine SDK.

- Install Google API client library for python into 'lib' directory by:

```
$ pip install -t lib -r requirements.txt
```

## Configuration

- Edit constants.py
    - Replace '{AN_UNIQUE_TOKEN}' with an arbitrary secret string of
      your choice to protect the endpoint from abuse.

## Deploy the application to App Engine

```
$ appcfg.py --oauth2 update -A your-application-id .
```

or you can use gcloud preview feature

```
$ gcloud preview app deploy --project your-application-id .
```

Then access the following URL:
  https://{your-application-id}.appspot.com/

## Run the application locally

```
$ dev_appserver.py -A your-application-id .
```
