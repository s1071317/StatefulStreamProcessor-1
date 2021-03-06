#!/usr/bin/env python3
import time
from datetime import datetime
import paho.mqtt.publish as publish
import json

# Note that MQTT publish is a bottleneck that can't publish more than 1000 S/s.
BROKER_HOST = "localhost"
BROKER_PORT = 1883
EVENT_FILE = "events.json"      # file of the records, not a json itself, but each row is
TOPIC_NAME = "machine/states"   # mqtt topic name to produce to
SAMPLE_RATE = 10              # sample rate in messages per second
READ_FIRST_N = None             # only read the first n lines of the file
SKIP_FIRST_N = 99000            # skip the first n lines of the file
TIMESHIFT = None


if __name__ == "__main__":
    st0 = st_t = time.time()
    interval = 1 / SAMPLE_RATE
    print("Starting the Simulator and publish the measurements via MQTT.")

    with open(EVENT_FILE) as f:
        events = f.readlines()

    i = 0
    try:
        # infinite loop to get a permanent stream
        while True:
            for j, line in enumerate(events):
                if j < SKIP_FIRST_N:
                    continue
                if "actSpeed" not in line and "vaTorque" not in line:
                    continue
                sent = False
                j = json.loads(line)
                if TIMESHIFT is None:
                    TIMESHIFT = int(datetime.now().timestamp()*1000) - j['Timestamp']
                j['Timestamp'] += TIMESHIFT
                while not sent:
                    try:
                        # publish with exactly-once delivery (pos=2)
                        publish.single(TOPIC_NAME, str(j).replace("'", '"'),
                                       hostname=BROKER_HOST, port=BROKER_PORT, qos=2)
                        sent = True
                    except OSError as e:
                        print("OSError, waiting a second and try again.")
                        time.sleep(1)

                # wait until the interval is exceeded
                while time.time() < st_t + interval:
                    time.sleep(0.01 * interval)
                st_t = time.time()
                time.sleep(0)

                i += 1
                # Read only the first n records of the event file
                if READ_FIRST_N:
                    if i >= READ_FIRST_N:
                        break
    except KeyboardInterrupt:
        print("Graceful stopped.")

    print(f"Finished in {(time.time() - st0) / i} s per publish. Wrote {i} records.")
