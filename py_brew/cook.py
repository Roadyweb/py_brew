'''
Created on Apr 12, 2015

@author: stefan
'''

import random
import threading
import time

THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

# Variables for simulation
SIMULATION = True
TEMP1=10.0
TEMP2=20.0
TEMP3=30.0

# Global variables for inter thread communication

status = {
          'thread': 'Not running',
          'temp1': 10.0,
          'temp2': 20.0,
          'temp3': 30.0,
          'relais1': 0,
          'relais2': 0,
          'relais3': 0
         }


# 0 = No change; 1 = Monitoring; 2 = Start cooking; 3 = Stop cooking; 4 = Exit
command = 0
cook_recipe = {}

class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        cook()
        print "Exiting " + self.name

def monitor():
    if SIMULATION:
        i = random.random()
        status['temp1'] = TEMP1 + i
        status['temp2'] = TEMP2 + i
        status['temp3'] = TEMP3 + i
        return
    # TODO read actual values from sensors
    pass

def control_temp():
    if SIMULATION:
        status['temp1'] += 1

def cook():
    global command
    command = 0
    status['thread'] = 'Idle'
    while 42:
        sleepduration = UPDATE_INT
        print 'Thread State: %s Command: %d' % (status['thread'], command)
        
        # Change thread state
        if command == 2:
            status['thread'] = 'Cooking'
        elif command == 3:
            status['thread'] = 'Monitoring'
        elif command == 4:
            status['thread'] = 'Not running'
            return

        # Start state specific tasks
        if status['thread'] == 'Monitoring':
            monitor()
        if status['thread'] == 'Cooking':
            control_temp()

        while sleepduration > 0:
            time.sleep(THREAD_SLEEP_INT)
            sleepduration -= THREAD_SLEEP_INT

