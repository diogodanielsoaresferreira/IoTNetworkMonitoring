import requests
import time

SENSOR_IPS = ["http://192.168.0.2:8080", "http://192.168.0.3:8080", "http://192.168.0.4:8080"]

SLEEP_SECONDS = 30

while True:
    for ip in SENSOR_IPS:
        time.sleep(SLEEP_SECONDS)
        r = requests.get(ip)
        print(r.text)