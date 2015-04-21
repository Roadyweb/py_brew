'''
Created on Apr 12, 2015

@author: stefan
'''

import datetime
import random
import threading
import time

import brewio
import wq

from helper import timedelta2sec


THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

TEMP_HYST = 1            # The range Temp +/- TEMP_HYST is valid

# Variables for simulation
SIMULATION = True
AMBIENT_TEMP = 10.0     # minimum temperature when no heating is applied
COOLING_FACTOR = 0.005  # cooling in degrees = (curr temp - AMBIENT_TEMP) / COOLING_FACTOR
HEATING_FACTOR = 0.4    # Normal heating is 1 K per second

# Global variables for inter thread communication
status = {
                  'tempk1': 10.0,
                  'tempk2': 20.0,
                  'pump1': 0,
                  'pump2': 0,
                  'heater': 0,
                  'cook_state': 'Off',
                  'pct_state': 'Not running',
                  'tmt_state': 'Not running',
                  'wqt_state': 'Not running',
                  'simulation': SIMULATION
                }


cook_recipe = {}

tpc = None


# Global variable to control ProcControlThread
# Possible values: ''      - no change 
#                  'START' - starts cooking
#                  'STOP'  - stops cooking

pct_req = ''


class ProcControlThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        status['pct_state'] = 'Not running'

    def run(self):
        print 'Starting ProcControlThread'
        self.cook()
        print 'Exiting ProcControlThread'

    def cook(self):
        global pct_req
        global tpc
        status['pct_state'] = 'Idle'
        while 42:
            if tpc == None:
                tpc = TempProcessControl(status)
            sleepduration = UPDATE_INT
            print 'PCT: State: %s - Req: %s' % (status['pct_state'], pct_req)

            # Change thread state
            if pct_req == 'START':
                status['pct_state'] = 'Cooking'
                tpc.start(cook_recipe)
            elif pct_req == 'STOP':
                status['pct_state'] = 'Idle'
                tpc.stop()
            elif pct_req == '':
                pass
            else:
                raise ValueError('Unsupported ProcControlThread request %s' % pct_req)
            pct_req = ''

            # Start state specific tasks
            if status['pct_state'] == 'Cooking':
                if tpc.control_temp_interval():
                    status['pct_state'] = 'Idle'
            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT


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

    def _get_temp_dura(self):
        return self.temp_list[self.cur_idx]

    def start(self, recipe):
        print 'TempProcessControl started. Recipe: %s' % recipe
        self.temp_list = recipe['list']
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
            if len(self.temp_list) <= self.cur_idx + 1:
                # Nothing more to do
                self.state = 'FINISHED'
                return
            self.cur_idx += 1
            self.set_temp, self.set_dura = self._get_temp_dura()
            self.state = 'INIT'

        elif self.state == 'FINISHED':
            self.status['cook_state'] = 'Finished'
            return True
        else:
            raise RuntimeError('TempProcessControl: Unknown state')
        print 'TempProcessControl State After: %s' % self.state

    def control_temp(self):
        ''' returns True whenr we have reached the current setpoint'''
        temp = status['tempk1']
        set_temp = self.set_temp
        if (set_temp - temp) > TEMP_HYST:
            # Too cold
            wq.heater_on_K1()
            return False
        elif (set_temp - temp) < (-1 * TEMP_HYST):
            # Too hot
            wq.heater_off_K1()
            return False
        else:
            # Right temperature
            wq.heater_off_K1()
            return True

    def stop(self):
        self.status['cook_state'] = 'Stopped'
        print 'TempProcessControl stopped'
        wq.heater_off_K1()
        wq.heater_off_K2()


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

