from matplotlib import pyplot as p
import random
from multiprocessing import Process, Value, Array
import signal
import sys
import requests
import time

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
import json

def sleep_show(sleep: float = 0.1):
    p.pause(sleep)


def start(hostname):
    requests.post(urljoin(hostname, 'api/v1/profiles/inventory/presets/default/start'))


def stop(hostname):
    requests.post(urljoin(hostname, 'api/v1/profiles/stop'))


def signal_handler(signal, frame):
    sys.exit(0)


def read_R700(hostname, cb, x, y, count, baseline):
    signal.signal(signal.SIGINT, signal_handler)
    for event in requests.get(urljoin(hostname, 'api/v1/data/stream'),
                              stream=True).iter_lines():
        cb(event, x, y, count, baseline)


def printR700(event, x, y, count):
    print(json.loads(event)["tagInventoryEvent"]["peakRssiCdbm"])

def writeR700(event, x, y, count, baseline):
    x[:] = [*x[1:], count.value]
    y[:] = [*y[1:], float(json.loads(event)["tagInventoryEvent"]["peakRssiCdbm"]) + baseline]

def xy_loop(x, y, count):
    while True:
        time.sleep(0.2)
        x[:] = [*x[1:], count.value]
        y[:] = [*y[1:], random.random()]
        count.value += 1


def show_plt(x, y, count, XMAX, sleeptime = 0.05):
    fig, ax = p.subplots(1, 1)
    now_x = (0, XMAX)
    ax.set_xlim(now_x)
    #ax.set_ylim((-6000, -1000))
    while True:
        line, = ax.plot(x, y, color="blue")
        if count.value > XMAX:
            now_x = (count.value - XMAX, count.value)
            ax.set_xlim(now_x)
        p.pause(sleeptime)
        line.remove()


def time_count(count, sleeptime = 0.05):
    while True:
        time.sleep(sleeptime)
        count.value += 1


if __name__ == '__main__':
    XMAX = 1000
    TIME = 0.04
    count = Value('i', 0)
    x = Array('f', XMAX*4)
    y = Array('f', XMAX*4)

    MatPlotProc = Process(target=show_plt, args=(x, y, count, XMAX, TIME,))
    R700Proc = Process(target=read_R700, args=("http://impinj-xx-xx-xx/", writeR700, x, y, count,6000,))
    TimeProc = Process(target=time_count, args=(count, TIME,))

    TimeProc.start()
    R700Proc.start()
    MatPlotProc.start()

    TimeProc.join()
    R700Proc.join()
    MatPlotProc.join()
