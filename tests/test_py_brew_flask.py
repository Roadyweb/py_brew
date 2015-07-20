'''
Created on Apr 24, 2015

@author: baumanst
'''

import os
import time
import unittest

import py_brew.cook as cook
import py_brew.config as config
import py_brew.helper as helper
import py_brew.myflask as flask


counter = 0

class TestFlask(unittest.TestCase):
    def setUp(self):
        global counter
        counter += 1
        print "SET UP", counter
        config.PCT_UPDATE_INT = 0.05
        flask.app.config['TESTING'] = True
        self.app = flask.app.test_client()
        print "SET UP END"

    def tearDown(self):
        global counter
        print "TEAR DOWN", counter
        counter -= 1
        flask.pct_thread.exit()
        flask.tmt_thread.exit()
        flask.wqt_thread.exit()
        flask.dlt_thread.exit()
        print "TEAR DOWN END"

    def testThreadsAreStarted(self):
        self.assertTrue(flask.pct_thread.is_alive(), 'PCT is not running')
        self.assertTrue(flask.tmt_thread.is_alive(), 'TMT is not running')
        self.assertTrue(flask.wqt_thread.is_alive(), 'WQT is not running')
        self.assertTrue(flask.dlt_thread.is_alive(), 'DLT is not running')

#===============================================================================
# class TestWebpageContents(unittest.TestCase):
#     def setUp(self):
#         flask.app.config['TESTING'] = True
#         self.app = flask.app.test_client()
# 
#     def tearDown(self):
#         flask.pct_thread.exit()
#         flask.tmt_thread.exit()
#         flask.wqt_thread.exit()
#         flask.dlt_thread.exit()
#===============================================================================

    def testWPRunFloat(self):
        ''' Renders the run webpage with given float status values and checks
            the correct rendering (one decimal place) of these values.
        '''

        ''' entires2test contains all 
            dict_key, line2grep
            pairs that should be tested
        '''
        entries2test = [['tempk1', '<td align="right">Temp K1:'],
                        ['tempk2', '<td align="right">Temp K2:'],
                        ['settempk1', '<td align="right">Set Temp K1:'],
                        ['settempk2', '<td align="right">Set Temp K2:'],
                        ['setdurak1', '<td align="right">Set Dura K1:'],
                        ['setdurak2', '<td align="right">Set Dura K2:'],
                       ]
        for dict_key, line2grep in entries2test:
            for value in range(-101, 150, 10):
                fvalue = value * 1.0    # convert to float
                cook.status[dict_key] = fvalue
                rv = self.app.get('/')
                line = helper.grepline(rv.data, line2grep)
                # print line, fvalue
                assert str(fvalue) in line

    def testWPRunInteger(self):
        ''' As above just for integer types '''
        entries2test = [['pump1', '<td align="right">Pumpe 1:'],
                        ['pump2', '<td align="right">Pumpe 2:'],
                        ['heater', '<td align="right">Heizung:'],
                       ]
        for dict_key, line2grep in entries2test:
            for value in range(0, 2):   # test 0 and 1
                cook.status[dict_key] = value
                rv = self.app.get('/')
                line = helper.grepline(rv.data, line2grep)
                # print line, value
                assert str(value) in line

    def testWPRunString(self):
        ''' As above just for string types '''
        entries2test = [['dlt_state', '<td align="right">DataLogger State:'],
                        ['pct_state', '<td align="right">ProcControl State:'],
                        ['wqt_state', '<td align="right">WorkQueue State:'],
                        ['tmt_state', '<td align="right">TempMon State:'],
                        ['cook_state', '<td align="right">Cook State:'],
                       ]
        strings2test = ['a', 'aa', 'Hallo', 'a very long string with spaces']
        for dict_key, line2grep in entries2test:
            for value in strings2test:
                cook.status[dict_key] = value
                rv = self.app.get('/')
                line = helper.grepline(rv.data, line2grep)
                # print line, value
                assert str(value) in line

    def testWPRunStartStopp(self):
        # Start with accessing /
        print 'START TEST1', cook.status['pct_state']
        print 'START TEST1', cook.status['pct_state']
        print 'START TEST1', cook.status['pct_state']
        print 'START TEST1', cook.status['pct_state']
        self.assertEqual(cook.status['pct_state'], 'Idle')
        self.app.post('/', data=dict(submit='Start'))
        print 'START TEST2', cook.status['pct_state']
        time.sleep(1)
        self.assertEqual(cook.status['pct_state'], 'Running')
        self.app.post('/', data=dict(submit='Stop'))
        time.sleep(0.3)
        self.assertEqual(cook.status['pct_state'], 'Idle')
        # and do it again with /run/
        self.app.post('/run/', data=dict(submit='Start'))
        time.sleep(0.3)
        self.assertEqual(cook.status['pct_state'], 'Running')
        self.app.post('/run/', data=dict(submit='Stop'))
        time.sleep(0.3)
        self.assertEqual(cook.status['pct_state'], 'Idle')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()