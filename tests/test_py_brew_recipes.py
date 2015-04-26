'''
Created on Apr 24, 2015

@author: baumanst
'''

import os
import unittest
import shutil

import py_brew.recipes as recipes
from py_brew.helper import str_timestamp_now

TST_DIR = 'test_recipes'


class Test(unittest.TestCase):
    def setUp(self):
        os.mkdir(TST_DIR)
        recipes.PATH = TST_DIR

    def tearDown(self):
        shutil.rmtree(TST_DIR)

    def testDefaultRecipe(self):
        # Start with no recipes in folder
        rcp = recipes.Recipes()
        self.assertEqual(
                rcp.get_selected_fname(),
                TST_DIR + '/' + recipes.DEF_RECIPE['name'] + recipes.EXT)
        recipe = rcp.get_selected_recipe()
        self.assertEqual(recipe['name'], recipes.DEF_RECIPE['name'])
        self.assertEqual(recipe['method'], recipes.DEF_RECIPE['method'])
        self.assertEqual(recipe['tempk1'], recipes.DEF_RECIPE['tempk1'])
        self.assertEqual(recipe['durak1'], recipes.DEF_RECIPE['durak1'])
        self.assertListEqual(recipe['list'], recipes.DEF_RECIPE['list'])

        self.assertEqual(len(rcp.get_fnames()), 1)

    def testAddSelectDeleteRecipe(self):
        rcp = recipes.Recipes()
        recipe = rcp.get_default()
        for i in range(2, 10):
            recipe = rcp.get_default()
            recipe['name'] = 'Default_Recipe' + str(i)
            rcp.save(recipe)
            self.assertEqual(len(rcp.get_fnames()), i, 'Add')
            rcp.select(i - 1)
            sel_recipe = rcp.get_selected_recipe()
            self.assertEqual(sel_recipe['name'], recipe['name'], 'Select')
            # Check timestamps, remove last 2 chars, since seconds might change
            self.assertEqual(sel_recipe['created'][:-2], str_timestamp_now()[:-2])
            self.assertEqual(sel_recipe['last_saved'][:-2], str_timestamp_now()[:-2])
        for i in range(9, 1, -1):
            rcp.delete(i - 1)
            self.assertEqual(len(rcp.get_fnames()), i - 1, 'Delete')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()