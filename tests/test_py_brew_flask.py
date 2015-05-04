'''
Created on Apr 24, 2015

@author: baumanst
'''

import os
import unittest
import tempfile

import py_brew.myflask as flask



class Test(unittest.TestCase):
    def setUp(self):
        flask.app.config['TESTING'] = True
        self.app = flask.app.test_client()

    def tearDown(self):
        flask.pct_thread.exit()
        flask.tmt_thread.exit()
        flask.wqt_thread.exit()
        flask.dlt_thread.exit()

    def testThreadsAreStarted(self):
        self.assertTrue(flask.pct_thread.is_alive(), 'PCT is not running')
        self.assertTrue(flask.tmt_thread.is_alive(), 'TMT is not running')
        self.assertTrue(flask.wqt_thread.is_alive(), 'WQT is not running')
        self.assertTrue(flask.dlt_thread.is_alive(), 'DLT is not running')

    def testRunPage(self):
        rv = self.app.get('/')
        assert 'Temp K1' in rv.data
        assert 'Temp K2' in rv.data


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()