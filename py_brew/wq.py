'''
Created on Apr 20, 2015

@author: baumanst
'''

import datetime
import threading
import time

import brewio
import config
import cook
from helper import timedelta2sec

# Variable to store instance for work queue thread and BlubberManager
wqt_thread = None
bm = None

heater_state_K1 = 0
heater_state_K2 = 0


class BlubberManager():
    ''' From time to time we have to switch on the pump for k2 to mix the
        stuff in pot 2
    '''
    def __init__(self, state_cb):
        self.waituntil = None
        self.set_state = state_cb
        self.state = 'INIT'
        self.set_state('Initialized')

    def start(self):
        if self.state == 'INIT':
            heater_off_K2()
            self.waituntil = datetime.datetime.now() + \
                datetime.timedelta(seconds=config.BLUBBER_INT)
            self.state = 'WAITING'
        elif self.state == 'WAITING':
            td2wait = timedelta2sec(self.waituntil - datetime.datetime.now())
            self.set_state('Waiting %d s' % td2wait)
            if td2wait < 0:
                self.waituntil = datetime.datetime.now() + \
                    datetime.timedelta(seconds=config.BLUBBER_DURA)
                # Finally start blubbering
                heater_on_K2()
                self.state = 'BLUBBERING'
                self.set_state('Blubbering')
        elif self.state == 'BLUBBERING':
            td2wait = timedelta2sec(self.waituntil - datetime.datetime.now())
            self.set_state('Blubbering %d s' % td2wait)
            if td2wait < 0:
                # We're done stop blubbering
                self.reset()
        else:
            raise RuntimeError('BM: Unknown state %s' % self.state)

    def reset(self):
        if self.state != 'INIT':
            heater_off_K2()
            self.state = 'INIT'
            self.set_state('Initialized')


def control_tempk1(set_temp):
    ''' returns True when we have reached the current setpoint'''
    tempk1 = cook.status['tempk1']
    if (set_temp - tempk1) > config.TEMP_HYST:
        # Too cold
        heater_on_K1()
        return False
    elif (set_temp - tempk1) < (-1 * config.TEMP_HYST):
        # Too hot
        heater_off_K1()
        return False
    else:
        # Right temperature
        heater_off_K1()
        return True


def control_tempk2(set_temp):
    ''' returns True when we have reached the current setpoint'''
    tempk2 = cook.status['tempk2']
    if (set_temp - tempk2) > config.TEMP_HYST:
        # Too cold
        heater_on_K2()
        bm.reset()
        return False
    elif (set_temp - tempk2) < (-1 * config.TEMP_HYST):
        # Too hot
        heater_off_K2()
        bm.reset()
        return False
    else:
        # Right temperature, we hand over control to the blubber manager
        bm.start()
        return True


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
        # Keep pump1 running all the time
        # wqt_thread.add_wq_item(brewio.pump1, 0, 10)
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
    global heater_state_K1
    global heater_state_K2
    wqt_thread.add_wq_item(brewio.heater, 0, 0)
    wqt_thread.add_wq_item(brewio.pump2, 0, 10)
    wqt_thread.add_wq_item(brewio.pump1, 0, 20)
    heater_state_K1 = 0
    heater_state_K2 = 0


class WorkQueueThread(threading.Thread):
    def __init__(self, state_cb):
        threading.Thread.__init__(self, name='WQT')
        self.queue = []
        self.set_state = state_cb
        self.exit_flag = False
        self.set_state('Initialized')

    def run(self):
        self.set_state('Running')
        while 42:
            sleepduration = config.WQ_UPDATE_INT
            # print 'WQT: queue length %d.' % (len(self.queue))
            if len(self.queue) > 0:
                el = self.queue[0]
                if el[2] < datetime.datetime.now():
                    # print 'WQT: exec %s. Len %d' % (el[0], len(self.queue))
                    func = el[0]
                    args = el[1]
                    func(args)
                    self.queue.pop(0)

            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(config.THREAD_SLEEP_INT)
                sleepduration -= config.THREAD_SLEEP_INT

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True

    def add_wq_item(self, func, args, offset_s):
        timestamp = datetime.datetime.now() + datetime.timedelta(seconds=offset_s)
        self.queue.append((func, args, timestamp))
