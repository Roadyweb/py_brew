'''
Created on Apr 22, 2015

@author: stefan
'''

import datetime
import threading
import time

import cook

from helper import timedelta2sec

THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 5.0         # seconds

class DataLoggerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = []
        cook.status['dlt_state'] = 'Initialized'
        self.data = {}
        self.data['list'] = []
        self.time_start = None
        self.log_flag = False

    def reset(self):
        self.time_start = datetime.datetime.now()
        self.data = {}
        self.data['list'] = []

    def run(self):
        print 'Starting DataLoggerThread'
        self.reset()
        while 42:
            sleepduration = UPDATE_INT
            if self.log_flag:
                cook.status['dlt_state'] = 'Logging'
                td = timedelta2sec(datetime.datetime.now() - self.time_start)
                entry = {}
                entry['time'] = td
                entry['tempk1'] = cook.status['tempk1']
                entry['tempk2'] = cook.status['tempk2']
                entry['settempk1'] = cook.status['settempk1']
                entry['settempk2'] = cook.status['settempk2']
                entry['pump1'] = cook.status['pump1']
                entry['pump2'] = cook.status['pump2']
                entry['heater'] = cook.status['heater']
                self.data['list'].append(entry)
                print 'DLT: record length %d.' % (len(self.data['list']))
            else:
                cook.status['dlt_state'] = 'Idle'
                self.reset()
            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

    def get_data(self):
        return self.data

    def start_logging(self):
        self.log_flag = True

    def stop_logging(self):
        self.log_flag = False

if __name__ == '__main__':
    pass