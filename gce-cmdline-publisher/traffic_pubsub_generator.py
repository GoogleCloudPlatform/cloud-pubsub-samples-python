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

"""
This script reads traffic sensor data from a file and publishes that data
to PubSub.  If you run it on a GCE instance, this instance must be
created with the "Cloud Platform" Project Access enabled. Click on
"Show advanced options" when creating the image to find this setting.

Before you run the script, create a PubSub topic, in the same project as the
GCE instance you will run on, to publish to. Edit the TOPIC variable in the
script to point to this topic.

Before you run this script, download an input data file (~2GB):
curl -O \
http://storage.googleapis.com/aju-sd-traffic/unzipped/Freeways-5Minaa2010-01-01_to_2010-02-15.csv
Or, for a smaller test file, you can use:
http://storage.googleapis.com/aju-sd-traffic/unzipped/Freeways-5Minaa2010-01-01_to_2010-02-15_test2.csv
These files contain real traffic sensor data from San Diego freeways.
See this file for copyright info:
http://storage.googleapis.com/aju-sd-traffic/freeway_detector_config/Freeways-Metadata-2010_01_01/copyright(san%20diego).txt

Usage:

Run the script like this to 'replay', with pauses in data publication
consistent with pauses in the series of data timestamps, which arrive every 5
minutes:
% python traffic_pubsub_generator.py --filename 'yourdatafile.csv' --replay

To restrict to N lines, do something like this:
% python traffic_pubsub_generator.py --filename 'yourdatafile.csv' \
  --num_lines 10 --replay

To alter the data timestamps to start from the script time, add
the --current flag.  If you want to set the topic from the command line, use
the --topic flag.
Run 'python traffic_pubsub_generator.py -h' for more information.
"""
import argparse
import base64
import csv
import datetime
import sys
import time

from apiclient import discovery
from dateutil.parser import parse
import httplib2
from oauth2client.client import GoogleCredentials

TOPIC = 'projects/your-project/topics/your-topic'  # default; set to your topic
LINE_BATCHES = 100  # report periodic progress

PUBSUB_SCOPES = ['https://www.googleapis.com/auth/pubsub']
NUM_RETRIES = 3


def create_pubsub_client():
    """Build the pubsub client."""
    credentials = GoogleCredentials.get_application_default()
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_SCOPES)
    http = httplib2.Http()
    credentials.authorize(http)
    return discovery.build('pubsub', 'v1beta2', http=http)


def publish(client, pubsub_topic, data_line):
    """Publish to the given pubsub topic."""
    pub = base64.urlsafe_b64encode(data_line)
    body = {'messages': [{'data': pub}]}
    resp = client.projects().topics().publish(
        topic=pubsub_topic, body=body).execute(num_retries=NUM_RETRIES)
    return resp


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", help="Replay in 'real time'",
                        action="store_true")
    parser.add_argument("--current",
                        help="Use date adjusted from script start time",
                        action="store_true")
    parser.add_argument("--filename", help="input filename")
    parser.add_argument("--num_lines", type=int, default=0,
                        help="The number of lines to process. " +
                        "0 indicates all.")
    parser.add_argument("--topic", default=TOPIC,
                        help="The pubsub topic to publish to. " +
                        "Should already exist.")
    args = parser.parse_args()

    pubsub_topic = args.topic
    print "Publishing to pubsub topic: %s" % pubsub_topic
    filename = args.filename
    print "filename: %s" % filename
    replay = args.replay
    print "replay mode: %s" % replay
    current = args.current
    print "current date mode: %s" % current
    num_lines = args.num_lines
    if num_lines:
        print "processing %s lines" % num_lines

    client = create_pubsub_client()
    dt = parse('01/01/2010 00:00:00')  # earliest date in the traffic files
    now = datetime.datetime.utcnow()
    # used if altering date to replay from start time
    diff = now - dt
    # used if running in 'replay' mode, reflecting pauses in the data
    prev_date = dt
    restart_time = now
    line_count = 0

    print "processing %s" % filename
    with open(filename) as data_file:
        reader = csv.reader(data_file)
        for line in reader:
            line_count += 1
            if num_lines:  # if terminating after num_lines processed
                if line_count >= num_lines:
                    print "Have processed %s lines" % num_lines
                    break
            if (line_count % LINE_BATCHES) == 0:
                print "%s lines processed" % line_count
            try:
                timestring = line[0]
                orig_date = parse(timestring)
                if current:  # if altering date to replay from start time
                    new_date = orig_date + diff
                    line[0] = new_date.strftime("%Y-%m-%d %H:%M:%S")
                if replay and orig_date != prev_date:
                    date_delta = orig_date - prev_date
                    print "date delta: %s" % date_delta.total_seconds()
                    current_time = datetime.datetime.utcnow()
                    timelapse = current_time - restart_time
                    print "timelapse: %s" % timelapse.total_seconds()
                    d2 = date_delta - timelapse
                    sleeptime = d2.total_seconds()
                    print "sleeping %s" % sleeptime
                    time.sleep(sleeptime)
                    restart_time = datetime.datetime.utcnow()
                    print "restart_time is set to: %s" % restart_time
                prev_date = orig_date
                publish(client, pubsub_topic, ",".join(line))
            except ValueError, e:
                sys.stderr.write("---Error: %s for %s\n" % (e, line))


if __name__ == '__main__':
        main(sys.argv)
