'''
Created on Apr 22, 2015

@author: stefan
'''

import datetime
import json
import threading
import time

import config

from helper import timedelta2sec, getsize


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

    def __init__(self, status, state_cb, socketio, log_interval=config.LOG_INT):
        """ Initializes all attributes """
        threading.Thread.__init__(self, name='DLT')
        self.status = status
        self.set_state = state_cb
        self.socketio = socketio
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
        while 42:
            sleepduration = self.log_interval
            if self.log_flag:
                # If we run the first time store start time as reference
                now = datetime.datetime.now()
                if self.time_start is None:
                    self.time_start = now
                self.set_state('Running')
                delta = timedelta2sec(now - self.time_start)
                entry = {}
                entry['time'] = delta
                # Put together a status string
                entry['state'] = (
                    self.status['cook_state'][0] +
                    str(self.status['cook_state_stage']) + '-' +
                    self.status['pct_state'][0] + '-' +
                    self.status['wqt_state'][0] + '-' +
                    self.status['dlt_state'][0] + '-' +
                    self.status['tmt_state'][0] + '-' +
                    self.status['bm_state'][0])
                entry['tempk1'] = self.status['tempk1']
                entry['tempk2'] = self.status['tempk2']
                entry['settempk1'] = self.status['settempk1']
                entry['settempk2'] = self.status['settempk2']
                entry['pump1'] = self.status['pump1']
                entry['pump2'] = self.status['pump2']
                entry['heater'] = self.status['heater']
                self.data['list'].append(entry)
                # Write log size back to global status dict
                self.status['log_size'] = getsize(self.data)
            else:
                self.set_state('Idle')

            self.socketio.emit('data', json.dumps(self.status),
                               broadcast=True)
            while sleepduration > 0:
                if self.exit_flag:
                    self.set_state('Not running')
                    return
                time.sleep(config.THREAD_SLEEP_INT)
                sleepduration -= config.THREAD_SLEEP_INT

    def get_data(self):
        """ Returns the current data as a list of dictonaries.
            Is empty if the thread wasn't started or has been stopped
        """
        return self.data

    def reset_data(self):
        """ Resets all logged data
        """
        self._reset()
        self.status['log_size'] = 0

    def start_logging(self):
        """ Starts the logging in the main loop """
        self._reset()
        self.log_flag = True

    def stop_logging(self):
        """ Stops the logging in the main loop """
        self.log_flag = False

    def exit(self):
        """ Exit the main loop """
        self.exit_flag = True
