'''
Created on Apr 12, 2015

@author: stefan
'''

import copy
import datetime
import threading
import time

import brewio
import config
import wq

from helper import timedelta2sec, timedelta2min


# Global variables for inter thread communication
status = {
                  'tempk1': 10.0,
                  'tempk2': 10.0,
                  'tempk1_offset': 0.0,
                  'hyst': config.TEMP_HYST,
                  'settempk1': 0.0,
                  'settempk2': 0.0,
                  'setdurak1': 0.0,
                  'setdurak2': 0.0,
                  'pump1': 0,
                  'pump2': 0,
                  'heater': 0,
                  'dlt_state': 'Not running',
                  'pct_state': 'Not running',
                  'pct_state_min_to_wait': '',
                  'wqt_state': 'Not running',
                  'tmt_state': 'Not running',
                  'bm_state': 'Unknown',
                  'cook_state': 'Off',
                  'cook_state_stage': '',
                  'cook_state_extended': '',
                  'simulation': config.SIMULATION,
                  'log_size': 0,
                  'recipe': None
                }

def dlt_state_cb(state):
    status['dlt_state'] = state

def pct_state_cb(state, min_to_wait=None, recipe=None):
    status['pct_state'] = state
    if min_to_wait is not None:
        status['pct_state_min_to_wait'] = min_to_wait
    else:
        status['pct_state_min_to_wait'] = ''
    if recipe is not None:
        status['recipe'] = recipe

def pct_get_state_cb():
    return status['pct_state']

def wqt_state_cb(state):
    status['wqt_state'] = state

def tmt_state_cb(state):
    status['tmt_state'] = state

def bm_state_cb(state):
    status['bm_state'] = state

def cook_state_cb(state, stage=None, extended=None):
    status['cook_state'] = state
    if stage is not None:
        status['cook_state_stage'] = stage
    else:
        status['cook_state_stage'] = ''
    if extended is not None:
        status['cook_state_extended'] = extended
    else:
        status['cook_state_extended'] = ''

def cook_temp_state_cb(settempk1, setdurak1, settempk2, setdurak2, tempk1_offset):
    status['settempk1'] = settempk1
    status['setdurak1'] = setdurak1
    status['settempk2'] = settempk2
    status['setdurak2'] = setdurak2
    status['tempk1_offset'] = tempk1_offset


class ProcControlThread (threading.Thread):
    """ Class to control the brewing process.

    It calls in regular intervals the TemperatureProcessControl. It runs as a
    thread.

    Attributes:
        state_cb: function to report back the current state of this thread
                  function takes a string as argument
        get_state_cb: function to get back the state from the global status
                      dict
    """
    def __init__(self, state_cb, get_state_cb, tpc):
        """ Initializes all attributes """
        threading.Thread.__init__(self, name='PCT')
        self.set_state = state_cb
        self.get_state = get_state_cb
        self.pct_req = ''   # Could be START, START_AT, STOP or EXIT
        self.recipe = None
        self.tpc = tpc
        self.start_at = None
        self.set_state('Initialized')

    def run(self):
        """ Main Loop """
        self.set_state('Idle')
        while 42:
            sleepduration = config.PCT_UPDATE_INT
            # print 'PCT: %s - Req: %s' % (self.get_state(), self.pct_req)

            # Change thread state
            if self.pct_req == 'START':
                self.set_state('Running', recipe=self.recipe)
                self.tpc.start(self.recipe)
            elif self.pct_req == 'START_AT':
                self.set_state('Waiting')
            elif self.pct_req == 'STOP':
                self.set_state('Idle')
                self.tpc.stop()
            elif self.pct_req == 'EXIT':
                self.set_state('Not running')
                return
            self.pct_req = ''

            # Start state specific tasks
            if self.get_state() == 'Running':
                if self.tpc.control_temp_interval():
                    self.set_state('Idle')

            if self.get_state() == 'Waiting':
                now = datetime.datetime.now()
                if now > self.start_at:
                    self.set_state('Running')
                    self.tpc.start(self.recipe)
                else:
                    min_to_wait = str(timedelta2min(self.start_at - now))
                    self.set_state('Waiting', min_to_wait + ' min')

            while sleepduration > 0:
                time.sleep(config.THREAD_SLEEP_INT)
                sleepduration -= config.THREAD_SLEEP_INT

    def start_cooking(self, recipe, start_at=None):
        """ Starts cookin in the main loop """
        self.recipe = copy.deepcopy(recipe)
        print start_at
        if start_at is None:
            print "Starting"
            self.pct_req = 'START'
        else:
            self.start_at = start_at
            print "Starting AT"
            self.pct_req = 'START_AT'

    def stop_cooking(self):
        """ Starts cooking in the main loop """
        self.pct_req = 'STOP'

    def exit(self):
        """ Exit the main loop """
        self.pct_req = 'EXIT'


class TempProcessControl(object):
    """Class to controls the different temperature stages of the brewing
       process.

    Attributes:
        state_cb: function to report back the current state of this thread
                  function takes a string as argument
        temp_state_cb: function to report back the current setpoint for tempk1,
                       durak1, tempk2 and durak2
    """
    def __init__(self, state_cb, temp_state_cb):
        """ Initializes all attributes """
        self.set_state = state_cb
        self.set_temp_state = temp_state_cb
        self.temp_list = []
        ''' Possible states:
                INIT:     New setpoint
                WAITING:  Setpoint reached, waiting for the required time
                FINISHED: Required time is over, go to next setpoint
        '''
        self.state = 'INIT'     # current state of the state machine
        self.cur_idx = 0
        self.wait_start = None
        self.method = None
        self.set_temp = None
        self.set_dura = None
        self.tempk1 = None
        self.durak1 = None
        self.tempk1_offset = 0.0

    def _get_temp_dura(self):
        """ Returns a tuple of the current temp and duration stage """
        tempk1_offset = self.tempk1 + self.tempk1_offset
        if self.method == 'K1':
            # TODO: use dummy values 0 for unset k2 parameters, to make flot
            # happy. Reevalute if necessary
            self.set_temp_state(
                    tempk1_offset, self.durak1, 0, 0, self.tempk1_offset
            )
            return (tempk1_offset, self.durak1)
        elif self.method == 'K2':
            temp, dura = self.temp_list[self.cur_idx]
            self.set_temp_state(
                    tempk1_offset, 10000, temp, dura, self.tempk1_offset
            )
            return (temp, dura)
        else:
            raise RuntimeError('Unsupported TempProcessControl method %s' % self.method)

    def start(self, recipe):
        print 'TempProcessControl started. Recipe: %s' % recipe
        self.temp_list = recipe['list']
        self.tempk1 = recipe['tempk1']
        self.durak1 = recipe['durak1']
        self.method = recipe['method']
        self.cur_idx = 0
        self.set_temp, self.set_dura = self._get_temp_dura()
        self.state = 'INIT'
        self.tempk1_offset = 0.0

    def control_temp_interval(self):
        ''' returns true when finished '''
        if self.state == 'INIT':
            self.set_state('Init', stage=self.cur_idx + 1)
            self.set_temp, self.set_dura = self._get_temp_dura()
            if self.control_temp() == True:
                self.state = 'WAITING'
                self.wait_start = datetime.datetime.now()
        elif self.state == 'WAITING':
            td_sec = timedelta2sec(datetime.datetime.now() - self.wait_start)
            self.set_state('Cooking',
                           stage=self.cur_idx + 1,
                           extended= '%d von %d sek'% (td_sec, self.set_dura))
            self.set_temp, self.set_dura = self._get_temp_dura()
            self.control_temp()
            if td_sec < self.set_dura:
                # We are not finished
                return

            # We are finished with the current stage, is there more to do?
            if self.method == 'K1' or len(self.temp_list) <= self.cur_idx + 1:
                # Nothing more to do
                self.state = 'FINISHED'
                return
            # Yes we have another stage
            self.cur_idx += 1
            self.tempk1_offset = 0.0
            self.set_temp, self.set_dura = self._get_temp_dura()
            self.state = 'INIT'

        elif self.state == 'FINISHED':
            self.set_state('Finished')
            wq.all_off()
            return True
        else:
            raise RuntimeError('TPC: Unknown state %s' % self.state)

    def stop(self):
        self.set_state('Stopped')
        wq.all_off()

    def inc_offset(self, offset):
        self.tempk1_offset += offset

    def dec_offset(self, offset):
        self.tempk1_offset -= offset

    def control_temp(self):
        ''' returns True when we have reached the current setpoint'''
        if self.method == 'K1':
            return wq.control_tempk1(self.set_temp)
        elif self.method == 'K2':
            wq.control_tempk1(self.tempk1 + self.tempk1_offset)
            return wq.control_tempk2(self.set_temp)
        else:
            raise RuntimeError('Unsupported TPC method %s' % self.method)


class TempMonThread (threading.Thread):
    """ Class to monitor temperature sensors in regular intervals.

    It runs as a thread.

    Attributes:
        state_cb: function to report back the current state of this thread.
                  The function takes a string as argument
    """
    def __init__(self, state_cb):
        """ Initializes all attributes """
        threading.Thread.__init__(self, name='TMT')
        self.set_state = state_cb
        self.set_state('Initialized')
        self.exit_flag = False

    def run(self):
        """ Main loop """
        self.set_state('Running')
        while 42:
            sleepduration = config.SENSOR_UPDATE_INT

            status['tempk1'] = brewio.tempk1()
            status['tempk2'] = brewio.tempk2()

            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(config.THREAD_SLEEP_INT)
                sleepduration -= config.THREAD_SLEEP_INT

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True

