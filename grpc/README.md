# cloud-pubsub-samples-python


## grpc

This is a command line sample application using the Cloud Pub/Sub API
via gRPC client library. The sample only lists topics in a given
project.

## Prerequisites

- Install grpc client library for Cloud Pub/Sub. Here is an example
  for installing it on your virtualenv environment.

```
$ virtualenv -p python2.7 --no-site-packages /some/dir
$ source /some/dir/bin/activate
$ pip install -r requirements.txt
```

## Register your application

- If you don't have a project, go to [Google Developers Console][1]
  and create a new project.

- Enable the "Google Cloud Pub/Sub" API under "APIs & auth > APIs."

- Go to "Credentials" and create a new Service Account.

- Select "Generate new JSON key", then download a new JSON file.

- Set the following environment variable.

  GOOGLE_APPLICATION_CREDENTIALS: the file path to the downloaded JSON file.

## Run the application

```
$ python pubsub_sample.py PROJECT_NAME
```

This will give you a list of topics in the given project.

Enjoy!

[1]: https://console.developers.google.com/project
