'''
Created on Apr 11, 2015

@author: stefan
'''

import copy
import os
import pickle

PATH = '../recipes/'
EXT = '.rcp'
'''
>>> datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
'2011-11-03 18:21:26'

'''
DEF_RECIPE = {
               'name': 'Test_Recipe',
               'date': '2011-11-03 18:21:26',
               'list': [
                        (40.0, 600),
                        (50.0, 300)
                       ]
              }

class Recipes(object):
    def __init__(self):
        self.recipes = []
        for dir_entry in os.listdir(PATH):
            dir_entry_path = os.path.join(PATH, dir_entry)
            if os.path.isfile(dir_entry_path):
                with open(dir_entry_path, 'r') as my_file:
                    try:
                        
                        self.recipes.append(pickle.load(my_file))
                        print 'Successfully loaded %s' % dir_entry_path
                    except EOFError, e:
                        print 'EOFError while loading %s. %s' % (dir_entry_path, e)
        
        # If no recipe is found, add at least one default recipe
        if len(self.recipes) == 0:
            self.recipes = copy.deepcopy(DEF_RECIPE)

    def get_default(self):
        return copy.deepcopy(DEF_RECIPE)

    def save(self, recipe):
        dir_entry_path = os.path.join(PATH, recipe['name'] + EXT)
        with open(dir_entry_path, 'wb') as my_file:
            pickle.dump(recipe, my_file)
