"""
This script reads traffic sensor data from a file and publishes that data
to PubSub.  It is intended to be run on a GCE instance. This instance must be
created with the "Cloud Platform" Project Access enabled. Click on
"Show advanced options" when creating the image to find this setting.
If you want to run the script locally (not on a GCE instance), you will need to
change the script to use a downloaded credentials file instead of the
GCE scopes.

Before you run the script, create a PubSub topic, in the same project as the
GCE instance you will run on, to publish to. Edit the TOPIC variable in the
script to point to this topic.

Before you run this script, download an input data file (~2GB):
curl -O http://storage.googleapis.com/aju-sd-traffic/unzipped/Freeways-5Minaa2010-01-01_to_2010-02-15.csv
Or, for a smaller test file, you can use:
http://storage.googleapis.com/aju-sd-traffic/unzipped/Freeways-5Minaa2010-01-01_to_2010-02-15_test2.csv
These files contain real traffic sensor data from San Diego freeways.  See this file for copyright info:
http://storage.googleapis.com/aju-sd-traffic/freeway_detector_config/Freeways-Metadata-2010_01_01/copyright(san%20diego).txt

Usage:

Run the script like this to 'replay', with pauses in data publication
consistent with pauses in the series of data timestamps, which arrive every 5
minutes:
% python traffic_pubsub_generator.py --filename 'yourdatafile.csv' --replay

To restrict to N lines, do something like this:
% python traffic_pubsub_generator.py --filename 'yourdatafile.csv' --num_lines 10 --replay

To alter the data timestamps to start from the script time, add
the --current flag.  If you want to set the topic from the command line, use
the --topic flag.
Run 'python traffic_pubsub_generator.py -h' for more information.
"""
import argparse
import httplib2
import base64
from dateutil.parser import parse
import datetime
import sys
import time

import oauth2client.gce as gce_oauth2client
from apiclient import discovery

TOPIC = 'projects/your-project/topics/your-topic'  # default - set to your topic
LINE_BATCHES = 100  # report periodic progress

PUBSUB_SCOPES = ['https://www.googleapis.com/auth/pubsub']
NUM_RETRIES = 3


def create_pubsub_client():
  credentials = gce_oauth2client.AppAssertionCredentials(
      scope=PUBSUB_SCOPES)
  http = httplib2.Http()
  credentials.authorize(http)
  return discovery.build('pubsub', 'v1beta2', http=http)


def get_date(line, date_diff, current):
  try:
    items = line.split(",")
    timestring = items[0]
    dt = parse(timestring)
    if current:  # if altering date to replay from start time
      new_date = dt + date_diff
      items[0] = new_date.strftime("%Y-%m-%d %H:%M:%S")
      newline = ",".join(items)
      return (newline, dt)
    else:
      return (line, dt)
  except ValueError, e:
    print "---Error: %s for %s" % (e, line)
    return None, None

def publish_reading(client, pubsub_topic, reading):
  pub = base64.b64encode(reading)
  body = {
      'messages': [{'data': pub}] }
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
                      help="The number of lines to process.  0 indicates all.")
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
  with open(filename) as inf:
    for line in inf:
      line_count += 1
      if num_lines:  # if terminating after num_lines processed
        if line_count >= num_lines:
          print "Have processed %s lines" % num_lines
          break
      if (line_count % LINE_BATCHES) == 0:
        print "%s lines processed" % line_count
      # print line
      (altered_line, orig_date) = get_date(line, diff, current)
      if altered_line:
        # print altered_line
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
        publish_reading(client, pubsub_topic, altered_line)

if __name__ == '__main__':
    main(sys.argv)
