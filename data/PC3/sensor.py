#!/usr/bin/env python

'''
	Simple aggregator for various sensor simulators
'''

from threading import Thread, Event
from time import sleep
import random
import datetime
import json
from confluent_kafka import Producer

'''
	Simulators period
'''
SIM_TEMPERATURE_PERIOD = 180

'''
	Event that manages a flag that can be set true or false
	It is used to finish each thread if the user wants to exit the program
'''
e = Event()

'''
	Kafka URL to POST
'''
KAFKA_URL = "172.16.238.11:9092"
SENSOR_ID_TEMP = "0"
p = Producer({'bootstrap.servers': KAFKA_URL})

'''
	Post a tuple <key, value> to kafka
'''


def send_to_kafka(key, value):
    p.produce("sensor_data", value.encode('utf-8'), key)
    p.flush()


'''
	Read temperature simulator
'''


def read_temperature_simulator():
    mean = 200
    variation = 100
    while (not e.isSet()):
        value = str(round((mean + random.uniform(-variation, variation)), 2))
        try:
            payload = {'value': value, 'timestamp': datetime.datetime.now().isoformat(), 'status': "dead"}
            send_to_kafka(SENSOR_ID_TEMP, json.dumps(payload))
            print("Value: %s sent." % (value))
        except:
            print("Error publishing temperature simulator values")
        sleep(SIM_TEMPERATURE_PERIOD)

'''
	Main function
	Program is initialized with the thread launching, waiting for the user to exit the program.
'''


def main():
    print('Simulators running. Press CTRL-C to interrupt...')

    thread_temperature = Thread(target=read_temperature_simulator)
    thread_temperature.start()

    while (thread_temperature.isAlive()):
        try:
            sleep(1)
        except KeyboardInterrupt:
            e.set()

            print('Exiting...')

            thread_temperature.join()

if __name__ == '__main__':
    main()
