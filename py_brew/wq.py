'''
Created on Apr 20, 2015

@author: baumanst
'''

import datetime
import threading
import time

import brewio
import cook

THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

# Variable to store instance for work queue thread
wqt_thread = None

heater_state_K1 = 0
heater_state_K2 = 0


def heater_on_K1():
    global heater_state_K1
    if heater_state_K1 == 0:
        wqt_thread.add_wq_item(brewio.heater, 1, 0)
        wqt_thread.add_wq_item(brewio.pump1, 1, 0)
        heater_state_K1 = 1

def heater_off_K1():
    global heater_state_K1
    if heater_state_K1 == 1:
        wqt_thread.add_wq_item(brewio.heater, 0, 0)
        wqt_thread.add_wq_item(brewio.pump1, 0, 0)
        heater_state_K1 = 0

def heater_on_K2():
    global heater_state_K2
    if heater_state_K2 == 0:
        wqt_thread.add_wq_item(brewio.pump2, 1, 0)
        heater_state_K2 = 1

def heater_off_K2():
    global heater_state_K2
    if heater_state_K2 == 1:
        wqt_thread.add_wq_item(brewio.pump2, 0, 0)
        heater_state_K2 = 0

def all_off():
    wqt_thread.add_wq_item(brewio.heater, 0, 0)
    wqt_thread.add_wq_item(brewio.pump2, 0, 10)
    wqt_thread.add_wq_item(brewio.pump1, 0, 20)
    pass


class WorkQueueThread(threading.Thread):
    def __init__(self, state_cb):
        threading.Thread.__init__(self, name='WQT')
        self.queue = []
        self.set_state = state_cb
        self.exit_flag = False
        self.set_state('Initialized')

    def run(self):
        print 'Starting WorkQueueThread'
        self.set_state('Running')
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
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True

    def add_wq_item(self, func, args, offset_s):
        timestamp = datetime.datetime.now() + datetime.timedelta(seconds=offset_s)
        self.queue.append((func, args, timestamp))