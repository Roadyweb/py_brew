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
                  'thread': 'Not running',
                  'simulation': SIMULATION
                }


# 0 = No change; 1 = Monitoring; 2 = Start cooking; 3 = Stop cooking; 4 = Exit
command = 0
cook_recipe = {}

tpc = None


class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        cook()
        print "Exiting " + self.name

def cook():
    global command
    global tpc
    command = 0
    status['thread'] = 'Idle'
    while 42:
        if tpc == None:
            tpc = TempProcessControl(status)
        sleepduration = UPDATE_INT
        print 'Thread State: %s Command: %d' % (status['thread'], command)
        
        # Change thread state
        if command == 2:
            status['thread'] = 'Cooking'
            tpc.start(cook_recipe)
        elif command == 3:
            status['thread'] = 'Monitoring'
            tpc.stop()
        elif command == 4:
            status['thread'] = 'Not running'
            return
        command = 0

        # Start state specific tasks
        if status['thread'] == 'Monitoring':
            tpc.monitor()
        if status['thread'] == 'Cooking':
            tpc.monitor()
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
        if SIMULATION:
            # parameters for simulation
            self.status['temp1'] = sim_calc_new_temp(self.status['temp1'], self.status['relais1'])
            self.status['temp2'] = sim_calc_new_temp(self.status['temp2'], self.status['relais2'])
            self.status['temp3'] = sim_calc_new_temp(self.status['temp3'], self.status['relais3'])
            return
        # TODO read actual values from sensors

    def stop(self):
        self.status['cook_state'] = 'Stopped'
        print 'TempProcessControl stopped'
        brewio.relais_off()


def sim_calc_new_temp(temp, heat):
    cooling = (temp - AMBIENT_TEMP) * COOLING_FACTOR
    noise = (random.random() - 0.5) / 2
    temp += noise + heat - cooling
    return temp
