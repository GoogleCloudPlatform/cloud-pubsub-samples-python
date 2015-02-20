
## 'Traffic Sensor' data generator script

The `traffic_pubsub_generator.py` script reads traffic sensor data from a file and publishes that data
to PubSub.  It is intended to be run on a [GCE](https://cloud.google.com/compute/docs/) instance, though can be adapted to run locally using downloaded credentials instead.
See the documentation in the script for more detail.