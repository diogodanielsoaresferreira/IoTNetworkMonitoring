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
import os

ip_list = ["http://192.168.0.2", "http://192.168.0.3", "http://192.168.0.4"]
mean_sleep = 60
mean_size = 50

def read_temperature_simulator():
    while (True):
        sleepTime = int((random.expovariate(1/mean_sleep)))
        try:
            os.system("sudo ifconfig eth0 192.168.0.10")
            r = requests.post(ip_list[random.randint(0, len(ip_list))-1], data={'data': 'd'*int(random.expovariate(1/mean_size))})
            os.system("sudo ifconfig eth0 192.168.0.1")
        except:
            print("Error publishing actuator values")
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
            print('Exiting...')
            thread_temperature.join()

if __name__ == '__main__':
    main()
