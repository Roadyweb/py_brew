'''
Created on Apr 24, 2015

@author: baumanst
'''
import unittest
import time

import py_brew.cook as cook
import py_brew.datalogger as datalogger

dlt = None

class Test(unittest.TestCase):
    def setUp(self):
        # For the test increase update speed
        self.dlt = datalogger.DataLoggerThread(cook.status, cook.dlt_state_cb, 0.01)

    def tearDown(self):
        self.dlt.exit()

    def testCookStatus(self):
        self.assertEqual(cook.status['dlt_state'], 'Initialized')

        self.dlt.start()
        time.sleep(0.1)
        self.assertEqual(cook.status['dlt_state'], 'Idle')

        self.dlt.start_logging()
        time.sleep(0.1)
        self.assertEqual(cook.status['dlt_state'], 'Logging')

        self.dlt.stop_logging()
        time.sleep(0.1)
        self.assertEqual(cook.status['dlt_state'], 'Idle')

        self.dlt.exit()
        time.sleep(0.1)
        self.assertEqual(cook.status['dlt_state'], 'Not running')

    def testGetData(self):
        EMPTY_DATA = {'list': []}
        self.assertEqual(self.dlt.get_data(), EMPTY_DATA)

        self.dlt.start()
        self.assertEqual(self.dlt.get_data(), EMPTY_DATA)

        self.dlt.start_logging()
        time.sleep(0.1)
        self.assertNotEqual(self.dlt.get_data(), EMPTY_DATA)

        # Check dedicated entries in dataset
        dl = self.dlt.get_data()['list']
        self.assertGreater(len(dl), 0)

        entry = dl[0]
        self.assertEqual(entry['time'], 0)
        self.assertEqual(entry['tempk1'], cook.status['tempk1'])
        self.assertEqual(entry['tempk2'], cook.status['tempk2'])
        self.assertEqual(entry['settempk1'], cook.status['settempk1'])
        self.assertEqual(entry['settempk2'], cook.status['settempk2'])
        self.assertEqual(entry['pump1'], cook.status['pump1'])
        self.assertEqual(entry['pump2'], cook.status['pump2'])
        self.assertEqual(entry['heater'], cook.status['heater'])

        self.dlt.stop_logging()
        time.sleep(0.2)
        self.assertEqual(self.dlt.get_data(), EMPTY_DATA)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()