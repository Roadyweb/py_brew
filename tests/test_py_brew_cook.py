'''
Created on Apr 24, 2015

@author: baumanst
'''
import unittest
import time

import py_brew.cook as cook
import py_brew.recipes as recipes
import py_brew.wq as wq

global wqt_thread

class Test(unittest.TestCase):
    def setUp(self):
        # For the test increase update speed
        cook.UPDATE_INT = 0.1
        tpc = cook.TempProcessControl(
                        cook.cook_state_cb,
                        cook.cook_temp_state_cb
                        )
        self.pct = cook.ProcControlThread(
                        cook.pct_state_cb,
                        cook.pct_get_state_cb,
                        tpc
                        )
        self.wqt_thread = wq.WorkQueueThread(cook.wqt_state_cb)
        self.wqt_thread.start()
        wq.wqt_thread = self.wqt_thread

    def tearDown(self):
        self.pct.exit()
        self.wqt_thread.exit()

    def testCookStatus(self):
        self.assertEqual(cook.status['pct_state'], 'Initialized')

        self.pct.start()
        time.sleep(0.1)
        self.assertEqual(cook.status['pct_state'], 'Idle')

        self.pct.start_cooking(recipes.DEF_RECIPE)
        time.sleep(1)
        self.assertEqual(cook.status['pct_state'], 'Running')

        self.pct.stop_cooking()
        time.sleep(0.5)
        self.assertEqual(cook.status['pct_state'], 'Idle')

        self.pct.exit()
        time.sleep(0.1)
        self.assertEqual(cook.status['pct_state'], 'Not running')

    def testGetData(self):
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()