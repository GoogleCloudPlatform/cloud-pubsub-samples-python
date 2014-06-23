cloud-pubsub-samples-python
===========================

appengine-push
--------------

Note: The push endpoints don't work with the App Engine's local
devserver. The push notifications will go to an HTTP URL on the App
Engine server even when you run this sample locally. So for now, we
recommend you deploy and run the app on App Engine.
TODO(tmatsuo): Better implementation for devserver.

= Register your application


1. Go to [Google Developers Console][1] and create a new project. This
   will automatically enable an App Engine application with the same
   ID as the project.

2. Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

3. For local development, also create a new client ID of type Service
   account. Save the private key with a strict permission.

= Prerequisites

- Install Python-2.7 and App Engine Python SDK. We recommend you
  install [Cloud SDK][2] rather than just installing App Engine SDK.

- For local development, you also need to install PyCrypto-2.6 or
  higher.

- Download google api client.
  Install Google API client library for python. Unzip
  google-api-python-client-gae-N.M.zip from our [downloads list][3]
  into a new 'lib' directory as described in our [documentation][4].

= Configuration

- Edit app.yaml
    - Replace 'your-application-id' with your real application id.

- Edit constants.py
    - Replace '{AN_UNIQUE_TOKEN}' with your random unique token.

- For local development, do the following too.
    - Replace '{YOUR_SERVICE_ACCOUNT_PRIVATE_KEY_FILE}' with the
      filename of the private key of your service account.
    - Replace '{SERVICE-ACCOUNT-EMAIL}' with the e-mail address of
      your service account.
    - Then access the following URL:
        https://{your-application-id}.appspot.com/

= Deploy the application to App Engine

  $ appcfg.py --oauth2 update .

  or you can use gcloud preview feature

  $ gcloud preview app deploy .

= Run the application locally

  $ dev_appserver.py

[1]: https://console.developers.google.com/project
[2]: https://developers.google.com/cloud/sdk/
[3]: https://code.google.com/p/google-api-python-client/downloads/list
[4]: https://developers.google.com/api-client-library/python/start/installation
