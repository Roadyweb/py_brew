'''
Created on Apr 12, 2015

@author: stefan
'''

import copy
import datetime
import threading
import time

import brewio
import wq

from helper import timedelta2sec


THREAD_SLEEP_INT = 0.05   # seconds
UPDATE_INT = 1            # seconds

# Global variables for inter thread communication
status = {
                  'tempk1': 10.0,
                  'tempk2': 10.0,
                  'settempk1': 0.0,
                  'settempk2': 0.0,
                  'setdurak1': 0.0,
                  'setdurak2': 0.0,
                  'pump1': 0,
                  'pump2': 0,
                  'heater': 0,
                  'dlt_state': 'Not running',
                  'pct_state': 'Not running',
                  'wqt_state': 'Not running',
                  'tmt_state': 'Not running',
                  'bm_state': 'Unknown',
                  'cook_state': 'Off',
                  'simulation': brewio.SIMULATION
                }

def dlt_state_cb(state):
    status['dlt_state'] = state

def pct_state_cb(state):
    status['pct_state'] = state

def pct_get_state_cb():
    return status['pct_state']

def wqt_state_cb(state):
    status['wqt_state'] = state

def tmt_state_cb(state):
    status['tmt_state'] = state

def bm_state_cb(state):
    status['bm_state'] = state

def cook_state_cb(state):
    status['cook_state'] = state

def cook_temp_state_cb(settempk1, setdurak1, settempk2, setdurak2):
    status['settempk1'] = settempk1
    status['setdurak1'] = setdurak1
    status['settempk2'] = settempk2
    status['setdurak2'] = setdurak2


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
        self.pct_req = ''   # Could be START, STOP or EXIT
        self.recipe = None
        self.tpc = tpc
        self.set_state('Initialized')

    def run(self):
        """ Main Loop """
        self.set_state('Idle')
        while 42:
            sleepduration = UPDATE_INT
            # print 'PCT: %s - Req: %s' % (self.get_state(), self.pct_req)

            # Change thread state
            if self.pct_req == 'START':
                self.set_state('Running')
                self.tpc.start(self.recipe)
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
            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

    def start_cooking(self, recipe):
        """ Starts cookin in the main loop """
        self.recipe = copy.deepcopy(recipe)
        self.pct_req = 'START'

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

    def _get_temp_dura(self):
        """ Returns a tuple of the current temp and duration stage """
        if self.method == 'K1':
            # TODO: use dummy values 10 for unset k2 parameters, to make flot
            # happy. Reevalute if necessary
            self.set_temp_state(self.tempk1, self.durak1, 10, 10)
            return (self.tempk1, self.durak1)
        elif self.method == 'K2':
            cur_temp_dura = self.temp_list[self.cur_idx]
            self.set_temp_state(self.tempk1, 10000, cur_temp_dura[0], cur_temp_dura[1])
            return cur_temp_dura
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

    def control_temp_interval(self):
        ''' returns true when finished '''
        if self.state == 'INIT':
            self.set_state('Stage %d - Init' % (self.cur_idx + 1))
            if self.control_temp() == True:
                self.state = 'WAITING'
                self.wait_start = datetime.datetime.now()
        elif self.state == 'WAITING':
            td_sec = timedelta2sec(datetime.datetime.now() - self.wait_start)
            self.set_state('Stage %d - Cooking for %d of of %d seconds' \
                % (self.cur_idx + 1, td_sec, self.set_dura)
                )
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

    def control_temp(self):
        ''' returns True when we have reached the current setpoint'''
        if self.method == 'K1':
            return wq.control_tempk1(self.set_temp)
        elif self.method == 'K2':
            wq.control_tempk1(self.tempk1)
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
            sleepduration = UPDATE_INT

            status['tempk1'] = brewio.tempk1()
            status['tempk2'] = brewio.tempk2()

            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True

