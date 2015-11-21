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

Before you run the script, create two PubSub topics, in the same project as the
GCE instance you will run on, to publish to. Edit the TRAFFIC_TOPIC and
INCIDENT_TOPIC variables in the script to point to these topics, or you can
pass in their names as command-line arguments.

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
the --current flag.
If you want to set the topics from the command line, use
the --topic and --incident_topic flags.
Run 'python traffic_pubsub_generator.py -h' for more information.
"""
import argparse
import base64
import csv
import datetime
import random
import sys
import time

from apiclient import discovery
from dateutil.parser import parse
from oauth2client.client import GoogleCredentials

# default; set to your traffic topic. Can override on command line.
TRAFFIC_TOPIC = 'projects/your-project/topics/your-topic'
# default; set to your incident topic.  Can override on command line.
INCIDENT_TOPIC = 'projects/your-project/topics/your-incident-topic'
LINE_BATCHES = 100  # report periodic progress

PUBSUB_SCOPES = ['https://www.googleapis.com/auth/pubsub']
NUM_RETRIES = 3
INCIDENT_TYPES = ['Traffic Hazard - Vehicle', 'Traffic Collision - No Details',
                  'Traffic Collision - No Injuries',
                  'Traffic Collision - Ambulance Responding',
                  'Hit and Run - No Injuries',
                  'Vehicle Fire', 'Pedestrian on a Highway', 'Animal on Road']
INCIDENT_DURATION_RANGE = 60  # max in minutes of a randomly generated duration
# The following value is used to determine whether an
# 'incident' is generated for a given reading. Increase/decrease this value
# to increase/decrease the likelihood that an incident is generated for a given
# reading.
INCIDENT_THRESH = 0.005


def create_pubsub_client():
    """Build the pubsub client."""
    credentials = GoogleCredentials.get_application_default()
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_SCOPES)
    return discovery.build('pubsub', 'v1beta2', credentials=credentials)


def publish(client, pubsub_topic, data_line, msg_attributes=None):
    """Publish to the given pubsub topic."""
    data = base64.b64encode(data_line)
    msg_payload = {'data': data}
    if msg_attributes:
        msg_payload['attributes'] = msg_attributes
    body = {'messages': [msg_payload]}
    resp = client.projects().topics().publish(
        topic=pubsub_topic, body=body).execute(num_retries=NUM_RETRIES)
    return resp


def maybe_add_delay(line, ts_int):
    """Randomly determine whether to simulate a publishing delay with this
    data element."""
    # 10 mins in ms.  Edit this value to change the amount of delay.
    ms_delay = 600000
    threshold = .005
    if random.random() < threshold:
        ts_int -= ms_delay  # generate 10-min apparent delay
        print line
        line[0] = "%s" % datetime.datetime.utcfromtimestamp(ts_int/1000)
        print ("Delaying ts attr %s, %s, %s" %
               (ts_int, datetime.datetime.utcfromtimestamp(ts_int/1000),
                line))
    return (line, ts_int)


def process_current_mode(orig_date, diff, line, replay, random_delays):
    """When using --current flag, modify original data to generate updated time
    information."""
    epoch = datetime.datetime(1970, 1, 1)
    if replay:  # use adjusted date from line of data
        new_date = orig_date + diff
        line[0] = new_date.strftime("%Y-%m-%d %H:%M:%S")
        ts_int = int(
            ((new_date - epoch).total_seconds() * 1000) +
            new_date.microsecond/1000)
        # 'random_delays' indicates whether to include random apparent delays
        # in published data
        if random_delays:
            (line, ts_int) = maybe_add_delay(line, ts_int)
        return (line, str(ts_int))
    else:  # simply using current time
        currtime = datetime.datetime.utcnow()
        ts_int = int(
            ((currtime - epoch).total_seconds() * 1000) +
            currtime.microsecond/1000)
        line[0] = currtime.strftime("%Y-%m-%d %H:%M:%S")
        # 'random_delays' indicates whether to include random apparent delays
        # in published data
        if random_delays:
            (line, ts_int) = maybe_add_delay(line, ts_int)
        return (line, str(ts_int))


def process_noncurrent_mode(orig_date, line, random_delays):
    """Called when not using --current flag; retaining original time
    information in data."""
    epoch = datetime.datetime(1970, 1, 1)
    ts_int = int(
        ((orig_date - epoch).total_seconds() * 1000) +
        orig_date.microsecond/1000)
    # 'random_delays' indicates whether to include random apparent delays
    # in published data
    if random_delays:
        (line, ts_int) = maybe_add_delay(line, ts_int)
    return (line, str(ts_int))


def publish_random_incident(client, incident_topic, incident_id,
                            timestamp, station_id, freeway, travel_direction,
                            msg_attributes=None):
    """Generate a random traffic 'incident' based on information from the
    given traffic reading, and publish it to the specified 'incidents' pubsub
    topic."""
    duration = random.randrange(INCIDENT_DURATION_RANGE)  # minutes
    cause = INCIDENT_TYPES[random.randrange(len(INCIDENT_TYPES))]
    data_line = '%s,%s,%s,%s,%s,%s,%s' % (incident_id, timestamp, duration,
                                          station_id, freeway,
                                          travel_direction, cause)
    print "incident data: %s" % data_line
    publish(client, incident_topic, data_line, msg_attributes)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", help="Replay in 'real time'",
                        action="store_true")
    parser.add_argument("--current",
                        help="Use date adjusted from script start time.",
                        action="store_true")
    parser.add_argument("--incidents",
                        help="Whether to generate and publish (fake) " +
                        "traffic incidents. Requires a second PubSub topic " +
                        "to be specified.",
                        action="store_true")
    parser.add_argument("--random_delays",
                        help="Whether to randomly alter the data to " +
                        "sometimes introduce delays between log date and " +
                        "publish timestamp.",
                        action="store_true")
    parser.add_argument("--filename", help="input filename")
    parser.add_argument("--num_lines", type=int, default=0,
                        help="The number of lines to process. " +
                        "0 indicates all.")
    parser.add_argument("--topic", default=TRAFFIC_TOPIC,
                        help="The pubsub 'traffic' topic to publish to. " +
                        "Should already exist.")
    parser.add_argument("--incident_topic", default=INCIDENT_TOPIC,
                        help="The pubsub 'incident' topic to publish to. " +
                        "Only used if the --incidents flag is set. " +
                        "If so, should already exist.")
    args = parser.parse_args()

    pubsub_topic = args.topic
    print "Publishing to pubsub 'traffic' topic: %s" % pubsub_topic
    incidents = args.incidents
    random_delays = args.random_delays
    if incidents:
        incident_topic = args.incident_topic
        print "Publishing to pubsub 'incident' topic: %s" % incident_topic
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
    incident_count = 0

    print "processing %s" % filename  # process the traffic data file
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
            ts = ""
            try:
                timestring = line[0]
                orig_date = parse(timestring)
                if current:  # if using --current flag
                    (line, ts) = process_current_mode(
                        orig_date, diff, line, replay, random_delays)
                else:  # not using --current flag
                    (line, ts) = process_noncurrent_mode(
                        orig_date, line, random_delays)

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
                msg_attributes = {'timestamp': ts}
                publish(client, pubsub_topic, ",".join(line), msg_attributes)
                if incidents:  # if generating traffic 'incidents' as well
                    # randomly determine whether we'll generate an incident
                    # associated with this reading.
                    if random.random() < INCIDENT_THRESH:
                        print "Generating a traffic incident for %s." % line
                        # grab the timestring, station id, freeway, and
                        # direction of travel.
                        # Then generate some 'incident' data and publish it to
                        # the incident topic.  Use the incident count as a
                        # simplistic id.
                        incident_count += 1
                        publish_random_incident(client, incident_topic,
                                                incident_count,
                                                line[0], line[1], line[2],
                                                line[3], msg_attributes)
            except ValueError, e:
                sys.stderr.write("---Error: %s for %s\n" % (e, line))


if __name__ == '__main__':
        main(sys.argv)
