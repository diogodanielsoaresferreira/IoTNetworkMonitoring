#!/usr/bin/env python

'''
	Simple aggregator for various sensor simulators
'''

from threading import Thread, Event
from time import sleep
import random
import datetime
import json
import requests


mean_sleep = 180
server_ips = ["http://192.168.100.1", "http://192.168.100.2", "http://192.168.100.3", "http://192.168.100.4", "http://192.168.100.5",
"http://192.168.100.6", "http://192.168.100.7", "http://192.168.100.8", "http://192.168.100.9", "http://192.168.100.10"]
mean_length = 30


'''
	Post a tuple <key, value> to kafka
'''

def send_value(ip, value):
    requests.post(ip, data=value)



def read_temperature_simulator():

    while (True):
        try:
            payload = {'value': 'a'*int(random.expovariate(1/mean_length))}
            send_value(server_ips[random.randint(0, len(server_ips)-1)], json.dumps(payload))
        except Exception as e:
            print(e)
            print("Error publishing temperature simulator values")
        sleep(random.expovariate(1/mean_sleep))


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
