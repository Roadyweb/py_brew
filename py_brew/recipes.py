'''
Created on Apr 11, 2015

@author: stefan
'''

import copy
import os
import pickle

from helper import str_timestamp_now

PATH = '../recipes/'
EXT = '.rcp'
'''
>>> datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
'2011-11-03 18:21:26'

'''
DEF_RECIPE = {
               'name': 'Default_Recipe',
               'created': '',
               'last_saved': '',
               'method': 'K1',
               'tempk1': 40.0,
               'durak1': 10,
               'list': [
                        (40.0, 600),
                        (50.0, 300)
                       ]
              }

class Recipes(object):
    """ Class to manage the different recipes

    It maintains two syncronized lists with filename and dicts of all
    avaiable recipes stored on the disk
    """
    def __init__(self):
        """
        Initializes all attributes and read available recipes from
        disk. If not available create the directory and store the default
        recipe.
        """
        self.recipes = []
        self.fnames = []
        if not os.path.isdir(PATH):
            os.makedirs(PATH)
        files = os.listdir(PATH)
        files.sort()
        for cur_file in files:
            file_path = os.path.join(PATH, cur_file)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as opened_file:
                    try:
                        self.recipes.append(pickle.load(opened_file))
                        self.fnames.append(file_path)
                        print 'Successfully loaded %s' % file_path
                    except EOFError, e:
                        print 'EOFError while loading %s. %s' % (file_path, e)
    
        # If no recipe is found, add at least one default recipe
        if len(self.recipes) == 0:
            def_recipe = copy.deepcopy(DEF_RECIPE)
            self.save(def_recipe)
        self.selected = 0

    def get_default(self):
        """ Return a copy of the default recipe """
        return copy.deepcopy(DEF_RECIPE)

    def get_fnames(self):
        """ Returns the list of all loaded file names """
        self.__init__()
        return self.fnames

    def get_selected_fname(self):
        """ Returns the selected file name """
        return self.fnames[self.selected]

    def get_selected_recipe(self):
        """ Returns the selected recipe """
        return self.recipes[self.selected]

    def save(self, recipe):
        """ Adds timestamps and saves the recipe provided as parameter """
        if 'created' not in recipe or recipe['created'] == '':
            recipe['created'] = str_timestamp_now()
        recipe['last_saved'] = str_timestamp_now()
        dir_entry_path = os.path.join(PATH, recipe['name'] + EXT)
        with open(dir_entry_path, 'wb') as my_file:
            pickle.dump(recipe, my_file)
        self.__init__()

    def delete(self, idx):
        """ Deletes the file provided as index of the internal arrays """
        fname = self.fnames[idx]
        try:
            os.remove(fname)
            print 'Successfully removed %s' % fname
        except:
            print 'Failed to remove %s' % fname
        self.__init__()

    def select(self, idx):
        """ Selects an recipe from the internal list as index """
        #TODO: some error checking is required here
        self.selected = idx
        print 'Selected entry %d' % idx
