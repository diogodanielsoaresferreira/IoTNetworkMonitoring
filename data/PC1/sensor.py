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
SIM_TEMPERATURE_PERIOD = 30

'''
	Event that manages a flag that can be set true or false
	It is used to finish each thread if the user wants to exit the program
'''
e = Event()

'''
	Kafka URL to POST
'''
SENSOR_ID_TEMP = "0"
#p = Producer({'bootstrap.servers': KAFKA_URL})

p = Producer({
    'bootstrap.servers': "velomobile-01.srvs.cloudkafka.com:9094, velomobile-02.srvs.cloudkafka.com:9094, velomobile-03.srvs.cloudkafka.com:9094",
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'},
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'SCRAM-SHA-256',
    'sasl.username': "48b34sa9",
    'sasl.password': "uxoX-yIGzXhrSCgfmJulInnnXMJyGDax"
})


'''
	Post a tuple <key, value> to kafka
'''

def send_to_kafka(key, value):
    p.produce("48b34sa9-default", value.encode('utf-8'), key)
    p.flush()


'''
	Read temperature simulator
'''


def read_temperature_simulator():
    mean = 20
    variation = 4
    while (not e.isSet()):
        value = str(round((mean + random.uniform(-variation, variation)), 2))
        try:
            payload = {'value': value, 'timestamp': datetime.datetime.now().isoformat(), 'status': "OK"}
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
