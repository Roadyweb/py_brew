'''
Created on Apr 11, 2015

@author: stefan
'''

import copy
import datetime
import os
import pickle

PATH = '../recipes/'
EXT = '.rcp'
'''
>>> datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
'2011-11-03 18:21:26'

'''
DEF_RECIPE = {
               'name': 'Default_Recipe',
               'created': '',
               'last_saved': '',
               'method': 'K1',
               'list': [
                        (40.0, 600),
                        (50.0, 300)
                       ]
              }

class Recipes(object):
    def __init__(self):
        self.recipes = []
        self.fnames = []
        for dir_entry in os.listdir(PATH):
            dir_entry_path = os.path.join(PATH, dir_entry)
            if os.path.isfile(dir_entry_path):
                with open(dir_entry_path, 'r') as my_file:
                    try:
                        
                        self.recipes.append(pickle.load(my_file))
                        self.fnames.append(dir_entry_path)
                        print 'Successfully loaded %s' % dir_entry_path
                    except EOFError, e:
                        print 'EOFError while loading %s. %s' % (dir_entry_path, e)
        
        # If no recipe is found, add at least one default recipe
        if len(self.recipes) == 0:
            self.recipes = copy.deepcopy(DEF_RECIPE)
        self.selected = 0

    def get_default(self):
        return copy.deepcopy(DEF_RECIPE)

    def get_fnames(self):
        self.__init__()
        return self.fnames

    def get_selected_fname(self):
        return self.fnames[self.selected]

    def get_selected_recipe(self):
        return self.recipes[self.selected]

    def save(self, recipe):
        if 'created' not in recipe or recipe['created'] == '':
            recipe['created'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        recipe['last_saved'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dir_entry_path = os.path.join(PATH, recipe['name'] + EXT)
        with open(dir_entry_path, 'wb') as my_file:
            pickle.dump(recipe, my_file)
        self.__init__()

    def delete(self, idx):
        fname = self.fnames[idx]
        try:
            os.remove(fname)
            print 'Successfully removed %s' % fname
        except:
            print 'Failed to remove %s' % fname
        self.__init__()

    def select(self, idx):
        self.selected = idx
        print 'Selected entry %d' % idx
