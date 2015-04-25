'''
Created on Apr 24, 2015

@author: baumanst
'''
import unittest
import time

import py_brew.cook as cook
import py_brew.recipes as recipes
import py_brew.wq as wq


class Test(unittest.TestCase):
    def setUp(self):
        # For the test increase update speed
        cook.UPDATE_INT = 0.1
        self.tmt = cook.TempMonThread(cook.tmt_state_cb)

    def tearDown(self):
        self.tmt.exit()

    def testCookStatus(self):
        self.assertEqual(cook.status['tmt_state'], 'Initialized')

        self.tmt.start()
        time.sleep(0.1)
        self.assertEqual(cook.status['tmt_state'], 'Running')

        self.tmt.exit()
        time.sleep(0.1)
        self.assertEqual(cook.status['tmt_state'], 'Not running')

    def testGetData(self):
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()