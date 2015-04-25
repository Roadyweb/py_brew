'''
Created on Apr 22, 2015

@author: stefan
'''

import datetime
import threading
import time

from py_brew.helper import timedelta2sec

THREAD_SLEEP_INT = 0.05  # seconds
LOG_INT = 5.0            # seconds

class DataLoggerThread(threading.Thread):
    """ Class to log data from the global status dictonary, add timestamps
        and provide it as a list.

    It runs as a thread.

    Attributes:
        status: reference to the global status dict, from where the data is
                copied
        state_cb: function to report back the current state of this thread
                  function takes a string as argument
        log_interval: log interval in seconds, defaults to 5
    """

    def __init__(self, status, state_cb, log_interval=LOG_INT):
        """ Initializes all attributes """
        threading.Thread.__init__(self, name='DLT')
        self.status = status
        self.set_state = state_cb
        self.log_interval = log_interval
        self.time_start = None
        self.log_flag = False
        self.exit_flag = False
        self.data = {}
        self._reset()
        self.set_state('Initialized')

    def _reset(self):
        """ Private function to reset the internal state of the thread """

        # self.data is dictionary and it's only entry is a list, it can be
        # expanded in the future, e.g. with the current recipes
        self.data = {}
        self.data['list'] = []
        self.time_start = None

    def run(self):
        """ Run is is the main worker loop for the data looger thread. It has
            to be started through threading.start()
        """
        self._reset()
        while 42:
            sleepduration = self.log_interval
            if self.log_flag:
                # If we run the first time store start time as reference
                if self.time_start == None:
                    self.time_start = datetime.datetime.now()
                self.set_state('Logging')
                delta = timedelta2sec(datetime.datetime.now() - self.time_start)
                entry = {}
                entry['time'] = delta
                entry['tempk1'] = self.status['tempk1']
                entry['tempk2'] = self.status['tempk2']
                entry['settempk1'] = self.status['settempk1']
                entry['settempk2'] = self.status['settempk2']
                entry['pump1'] = self.status['pump1']
                entry['pump2'] = self.status['pump2']
                entry['heater'] = self.status['heater']
                self.data['list'].append(entry)
                print 'DLT: record length %d.' % (len(self.data['list']))
            else:
                self.set_state('Idle')
                self._reset()
            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(THREAD_SLEEP_INT)
                sleepduration -= THREAD_SLEEP_INT

    def get_data(self):
        """ Returns the current data as a list of dictonaries.
            Is empty if the thread wasn't started or has been stopped
        """
        return self.data

    def start_logging(self):
        """ Starts the logging in the main loop """
        self.log_flag = True

    def stop_logging(self):
        """ Stops the logging in the main loop """
        self.log_flag = False

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True
