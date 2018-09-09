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


'''
	Event that manages a flag that can be set true or false
	It is used to finish each thread if the user wants to exit the program
'''
e = Event()

'''
	Read temperature simulator
'''


def read_temperature_simulator():
    ip_list = ["http://192.168.0.254", "http://192.168.0.1", "http://192.168.0.2", "http://192.168.0.3"]
    index = 0
    mean = 600
    variation = 300
    while (not e.isSet()):
        sleepTime = int((mean + random.uniform(-variation, variation)))
        try:
            r = requests.post(ip_list[index], data={'data': 'data1'})
            index = (index + 1) % len(ip_list)
        except e:
            print(e)
            print("Error publishing temperature simulator values")
        sleep(sleepTime)

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

