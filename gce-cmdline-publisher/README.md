
## 'Traffic Sensor' data generator script

The `traffic_pubsub_generator.py` script reads traffic sensor data from a file and publishes that data
to a PubSub topic.
The script uses the [ Google APIs Client Library for Python](https://developers.google.com/api-client-library/python/?_ga=1.268664177.1432014927.1424389293).
You can install this library via:

```
pip install --upgrade google-api-python-client
```

See [this page](https://developers.google.com/accounts/docs/application-default-credentials)
for more information about the `GoogleCredentials` library used by the script.

See the documentation in `traffic_pubsub_generator.py` for more detail.
