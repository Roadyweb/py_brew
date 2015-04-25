'''
Created on Apr 12, 2015

@author: stefan
'''

import copy
import datetime
import random
import threading
import time

import wq

from helper import timedelta2sec


THREAD_SLEEP_INT = 0.05   # seconds
UPDATE_INT = 1            # seconds

TEMP_HYST = 1             # The range Temp +/- TEMP_HYST is valid

# Variables for simulation
SIMULATION = True
AMBIENT_TEMP = 10.0     # minimum temperature when no heating is applied
COOLING_FACTOR = 0.005  # cooling in degrees = (curr temp - AMBIENT_TEMP) / COOLING_FACTOR
HEATING_FACTOR = 0.4    # Normal heating is 1 K per second

# Global variables for inter thread communication
status = {
                  'tempk1': 10.0,
                  'tempk2': 20.0,
                  'settempk1': 10.0,
                  'settempk2': 20.0,
                  'setdurak1': 10.0,
                  'setdurak2': 20.0,
                  'pump1': 0,
                  'pump2': 0,
                  'heater': 0,
                  'cook_state': 'Off',
                  'pct_state': 'Not running',
                  'tmt_state': 'Not running',
                  'wqt_state': 'Not running',
                  'dlt_state': 'Not running',
                  'simulation': SIMULATION
                }

def dlt_state_cb(state):
    status['dlt_state'] = state

def pct_state_cb(state):
    status['pct_state'] = state

def wqt_state_cb(state):
    status['wqt_state'] = state

class ProcControlThread (threading.Thread):
    def __init__(self, state_cb):
        threading.Thread.__init__(self)
        self.set_state = state_cb
        self.pct_req = ''
        self.recipe = None
        self.exit_flag = False
        self.tpc = TempProcessControl(status)
        self.set_state('Initialized')

    def run(self):
        print 'Starting ProcControlThread'
        self.cook()
        print 'Exiting ProcControlThread'

    def cook(self):
        self.set_state('Idle')
        while 42:
            sleepduration = UPDATE_INT
            print 'PCT: State: %s - Req: %s' % (status['pct_state'], self.pct_req)

            # Change thread state
            if self.pct_req == 'START':
                self.set_state('Running')
                self.tpc.start(self.recipe)
            elif self.pct_req == 'STOP':
                self.set_state('Idle')
                self.tpc.stop()
            self.pct_req = ''

            # Start state specific tasks
            if status['pct_state'] == 'Running':
                if self.tpc.control_temp_interval():
                    self.set_state('Idle')
            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
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
        self.exit_flag = True

class TempProcessControl(object):
    '''Controls the different temperature stages'''
    def __init__(self, status):
        print 'TempProcessControl init'
        self.temp_list = []
        ''' Possible states:
                INIT:     New setpoint
                WAITING:  Setpoint reached, waiting for the required time
                FINISHED: Required time is over, go to next setpoint
        '''
        self.state = 'INIT'     # current state of the state machine
        self.status = status    # reference to global status dict
        self.cur_idx = 0
        self.wait_start = None
        self.method = None
        self.set_temp = None
        self.set_dura = None
        self.tempk1 = None
        self.durak1 = None

    def _get_temp_dura(self):
        if self.method == 'K1':
            status['settempk1'] = self.tempk1
            status['setdurak1'] = self.durak1
            # TODO: use dummy values for unset k2 parameters, to make flot
            # happy. Reevalute if necessary
            status['settempk2'] = 10
            status['setdurak2'] = 10
            return (self.tempk1, self.durak1)
        elif self.method == 'K2':
            cur_temp_dura = self.temp_list[self.cur_idx]
            status['settempk1'] = self.tempk1
            status['setdurak1'] = 100000    # dummy value
            status['settempk2'] = cur_temp_dura[0]
            status['setdurak2'] = cur_temp_dura[1]
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
        print 'TempProcessControl State Before: %s' % self.state

        if self.state == 'INIT':
            self.status['cook_state'] = 'Init'
            if self.control_temp() == True:
                self.state = 'WAITING'
                self.wait_start = datetime.datetime.now()
        elif self.state == 'WAITING':
            td = datetime.datetime.now() - self.wait_start
            status['cook_state'] = 'Stage %d - Cooking for %d of a total of %d seconds' \
                % (self.cur_idx + 1, timedelta2sec(td), self.set_dura)
            self.control_temp()
            if timedelta2sec(td) < self.set_dura:
                # We are not finished
                return

            # We are finished with the current stage
            if self.method == 'K1' or len(self.temp_list) <= self.cur_idx + 1:
                # Nothing more to do
                self.state = 'FINISHED'
                return
            self.cur_idx += 1
            self.set_temp, self.set_dura = self._get_temp_dura()
            self.state = 'INIT'

        elif self.state == 'FINISHED':
            self.status['cook_state'] = 'Finished'
            wq.all_off()
            return True
        else:
            raise RuntimeError('TempProcessControl: Unknown state %s' % self.state)
        print 'TempProcessControl State After: %s' % self.state

    def control_temp(self):
        ''' returns True when we have reached the current setpoint'''
        if self.method == 'K1':
            return self.control_tempk1(self.set_temp)
        elif self.method == 'K2':
            self.control_tempk1(self.tempk1)
            return self.control_tempk2(self.set_temp)
        else:
            raise RuntimeError('Unsupported TempProcessControl method %s' % self.method)

    def control_tempk1(self, set_temp):
        ''' returns True when we have reached the current setpoint'''
        tempk1 = status['tempk1']
        if (set_temp - tempk1) > TEMP_HYST:
            # Too cold
            wq.heater_on_K1()
            return False
        elif (set_temp - tempk1) < (-1 * TEMP_HYST):
            # Too hot
            wq.heater_off_K1()
            return False
        else:
            # Right temperature
            wq.heater_off_K1()
            return True

    def control_tempk2(self, set_temp):
        ''' returns True when we have reached the current setpoint'''
        tempk2 = status['tempk2']
        if (set_temp - tempk2) > TEMP_HYST:
            # Too cold
            wq.heater_on_K2()
            return False
        elif (set_temp - tempk2) < (-1 * TEMP_HYST):
            # Too hot
            wq.heater_off_K2()
            return False
        else:
            # Right temperature
            wq.heater_off_K2()
            return True

    def stop(self):
        self.status['cook_state'] = 'Stopped'
        print 'TempProcessControl stopped'
        wq.all_off()


class TempMonThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        status['tmt_state'] = 'Not running'
    def run(self):
        status['tmt_state'] = 'Running'
        print 'Starting TempMonThread'
        self.monitor()
        print 'Exiting TempMonThread'
        status['tmt_state'] = 'Not running'

    def monitor(self):
        while 42:
            sleepduration = UPDATE_INT

            if SIMULATION:
                status['tempk1'] = sim_calc_new_temp(status['tempk1'], status['pump1'])
                status['tempk2'] = sim_calc_new_temp(status['tempk2'], status['pump2'])

            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

def sim_calc_new_temp(temp, heat):
    cooling = (temp - AMBIENT_TEMP) * COOLING_FACTOR
    heating = heat * HEATING_FACTOR
    noise = (random.random() - 0.5) / 2
    temp += noise + heating - cooling
    return temp

