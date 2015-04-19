'''
Created on Apr 12, 2015

@author: stefan
'''

import datetime
import random
import threading
import time

import brewio

from helper import timedelta2sec


THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

TEMP_HYST = 1            # The range Temp +/- TEMP_HYST is valid

# Variables for simulation
SIMULATION = True
AMBIENT_TEMP = 10.0     # minimum temperature when no heating is applied
COOLING_FACTOR = 0.01   # cooling in degrees = (curr temp - AMBIENT_TEMP) / COOLING_FACTOR


# Global variables for inter thread communication
status = {
                  'temp1': 10.0,
                  'temp2': 20.0,
                  'temp3': 30.0,
                  'relais1': 0,
                  'relais2': 0,
                  'relais3': 0,
                  'cook_state': 'Off',
                  'pct_state': 'Not running',
                  'tmt_state': 'Not running',
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
        print "Starting ProcControlThread"
        self.cook()
        print "Exiting ProcControlThread"

    def cook(self):
        global pct_req
        global tpc
        status['pct_state'] = 'Idle'
        while 42:
            if tpc == None:
                tpc = TempProcessControl(status)
            sleepduration = UPDATE_INT
            print 'PCT State: %s - Req: %s' % (status['pct_state'], pct_req)
            
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
                tpc.control_temp()
    
            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT


class TempProcessControl(object):
    '''Controls the different temperature stage'''
    def __init__(self, status):
        print 'TempProcessControl init'
        self.temp_list = []
        ''' Possible states:
                Init: New setpoint
                Wait: Setpoint reached, waiting for the required time
                Finished: Required time is over, go to next setpoint
        '''
        self.state = 'Init'     # current state of the state machine
        self.status = status    # reference to global status dict
        self.cur_idx = 0
        self.wait_start = None
        self.set_temp = None
        self.set_dura = None

    def _get_temp_dura(self):
        return self.temp_list[self.cur_idx]

    def start(self, recipe):
        print 'TempProcessControl started. Recipe: %s' % recipe
        self.temp_list = recipe['list']
        self.cur_idx = 0
        self.set_temp, self.set_dura = self._get_temp_dura()

    def control_temp(self):
        print 'TempProcessControl State Before: %s' % self.state

        if self.state == 'Init':
            self.status['cook_state'] = 'Init'
            temp = status['temp1']
            set_temp = self.set_temp
            if (set_temp - temp) > TEMP_HYST:
                # Too cold
                brewio.relais1(1)
                self.status['relais1'] = 1
            elif (set_temp - temp) < (-1 * TEMP_HYST):
                # Too hot
                brewio.relais1(0)
                self.status['relais1'] = 0
            else:
                # Right temperature
                brewio.relais1(0)
                self.status['relais1'] = 0
                self.state = 'Waiting'
                self.wait_start = datetime.datetime.now()

        elif self.state == 'Waiting':
            td = datetime.datetime.now() - self.wait_start
            status['cook_state'] = 'Stage %d - Cooking for %d of a total of %d seconds' \
                % (self.cur_idx + 1, timedelta2sec(td), self.set_dura)
            if timedelta2sec(td) < self.set_dura:
                # We are not finished
                return

            # We are finished with the current stage
            self.cur_idx += 1
            if (len(self.temp_list) - 1) <= self.cur_idx:
                # Nothing more to do
                self.state = 'Finished'
            self.set_temp, self.set_dura = self._get_temp_dura()
            self.state = 'Init'

        elif self.state == 'Finished':
            self.status['cook_state'] = 'Finished'
            self.status['relais1'] = 0
            brewio.relais_off()
        else:
            raise RuntimeError('TempProcessControl: Unknown state')
        print 'TempProcessControl State After: %s' % self.state

    def monitor(self):
            return
        # TODO read actual values from sensors

    def stop(self):
        self.status['cook_state'] = 'Stopped'
        print 'TempProcessControl stopped'
        brewio.relais_off()


class TempMonThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        status['tmt_state'] = 'Not running'
    def run(self):
        status['tmt_state'] = 'Running'
        print "Starting TempMonThread"
        self.monitor()
        print "Exiting TempMonThread"
        status['tmt_state'] = 'Not running'

    def monitor(self):
        while 42:
            sleepduration = UPDATE_INT

            if SIMULATION:
                status['temp1'] = sim_calc_new_temp(status['temp1'], status['relais1'])
                status['temp2'] = sim_calc_new_temp(status['temp2'], status['relais2'])
                status['temp3'] = sim_calc_new_temp(status['temp3'], status['relais3'])
    
            while sleepduration > 0:
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

def sim_calc_new_temp(temp, heat):
    cooling = (temp - AMBIENT_TEMP) * COOLING_FACTOR
    noise = (random.random() - 0.5) / 2
    temp += noise + heat - cooling
    return temp

