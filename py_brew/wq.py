'''
Created on Apr 20, 2015

@author: baumanst
'''

import datetime
import threading
import time

import brewio

THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

# Variable to store instance for work queue thread
wqt_thread = None

heater_state_K1 = 0
heater_state_K2 = 0

def heater_on(method):
    if method == 'K1':
        heater_on_K1()
    elif method == 'K2':
        heater_on_K2()
    else:
        raise RuntimeError('Unsupported method: %s' % method)

def heater_off(method):
    if method == 'K1':
        heater_off_K1()
    elif method == 'K2':
        heater_off_K2()
    else:
        raise RuntimeError('Unsupported method: %s' % method)

def switch_off(method):
    if method == 'K1':
        switch_off_K1()
    elif method == 'K2':
        switch_off_K2()
    else:
        raise RuntimeError('Unsupported method: %s' % method)

def heater_on_K1():
    global heater_state_K1
    if heater_state_K1 == 0:
        wqt_thread.add_wq_item(brewio.relais1, 1, 5)
        wqt_thread.add_wq_item(brewio.relais2, 1, 10)
        wqt_thread.add_wq_item(brewio.relais3, 1, 15)
        heater_state_K1 = 1

def heater_on_K2():
    pass

def heater_off_K1():
    global heater_state_K1
    if heater_state_K1 == 1:
        wqt_thread.add_wq_item(brewio.relais1, 0, 5)
        wqt_thread.add_wq_item(brewio.relais2, 0, 10)
        wqt_thread.add_wq_item(brewio.relais3, 0, 15)
        heater_state_K1 = 0

def heater_off_K2():
    pass

def switch_off_K1():
    pass

def switch_off_K2():
    pass


class WorkQueueThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = []

    def run(self):
        print 'Starting WorkQueueThread'
        sleepduration = UPDATE_INT
        while 42:
            sleepduration = UPDATE_INT
            print 'WQT: queue length %d.' % (len(self.queue))
            if len(self.queue) > 0:
                el = self.queue[0]
                if el[2] < datetime.datetime.now():
                    print 'WQT: executing %s' % el[0]
                    func = el[0]
                    args = el[1]
                    func(args)
                    self.queue.pop(0)

            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT
        print 'Exiting WorkQueueThread'

    def add_wq_item(self, func, args, offset_s):
        timestamp = datetime.datetime.now() + datetime.timedelta(seconds=offset_s)
        self.queue.append((func, args, timestamp))