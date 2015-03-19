# cloud-pubsub-samples-python

## appengine-push

Note: The push endpoints don't work with the App Engine's local
devserver. The push notifications will go to an HTTP URL on the App
Engine server even when you run this sample locally. So we recommend
you deploy and run the app on App Engine.
TODO(tmatsuo): Better implementation for devserver.

## Register your application

- Go to [Google Developers Console][1] and create a new project. This
  will automatically enable an App Engine application with the same ID
  as the project.

- Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

- For local development also follow the instructions below.

  - Go to "Credentials" and create a new Service Account.

  - Select "Generate new JSON key", then download a new JSON file.

  - Set the following environment variable.

    GOOGLE_APPLICATION_CREDENTIALS: the file path to the downloaded JSON file.

## Prerequisites

- Install Python-2.7 and App Engine Python SDK. We recommend you
  install [Cloud SDK][2] rather than just installing App Engine SDK.

- For local development, you also need to install PyCrypto-2.6 or
  higher.

- Install Google API client library for python by invoking:

  $ sh scripts/setup-google-api-client.sh .

## Configuration

- Edit app.yaml
    - Replace 'your-application-id' with your real application id. If
      you will use the new gcloud preview feature, you may comment out
      this entire line by prefxing the line with a '#'. The
      application field is deprecated and not used by gcloud.

- Edit constants.py
    - Replace '{AN_UNIQUE_TOKEN}' with your random unique token.

## Deploy the application to App Engine

```
$ appcfg.py --oauth2 update .
```

or you can use gcloud preview feature

```
$ gcloud preview app deploy . --project your-application-id
```

Then access the following URL:
  https://{your-application-id}.appspot.com/

## Run the application locally

```
$ dev_appserver.py
```

[1]: https://console.developers.google.com/project
[2]: https://developers.google.com/cloud/sdk/
