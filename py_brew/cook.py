'''
Created on Apr 12, 2015

@author: stefan
'''


import threading
import time

THREAD_SLEEP_INT = 0.1   # seconds
UPDATE_INT = 1.0         # seconds

# Global variables for inter thread communication

# 0 = Idle; 1 = Monitoring; 2 = Cooking
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
exit_flag = False


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
    command = 0
    status['thread'] = 'Idle'
    while 42:
        sleepduration = UPDATE_INT
        print 'Thread State: %s Command: %d' % (status['thread'], command)
        if command == 2:
            status['thread'] = 'Cooking'
        elif command == 3:
            status['thread'] = 'Monitoring'
        elif command == 4:
            status['thread'] = 'Exiting'
            return
        while sleepduration > 0:
            time.sleep(THREAD_SLEEP_INT)
            sleepduration -= THREAD_SLEEP_INT
            if exit_flag:
                print "Exit thread"
                return

