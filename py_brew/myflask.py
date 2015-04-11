#!/usr/bin/env python
'''
Created on 10.07.2012
@author: baumanst

Main functions to create the webpages
'''

import simplejson as json
import jsonpickle
import pickle
import tempfile
import copy

from datetime import datetime
from flask import Flask, request, render_template, abort, send_file
from recipes import Recipes

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')



status = {
          'thread': 'Running',
          'temp1': 10.0,
          'temp2': 20.0,
          'temp3': 30.0
         }

last_action = 'Empty'

recipes = Recipes()
brew_recipe = recipes.get_default()

@app.errorhandler(IOError)
def special_exception_handler(error):
    return render_template('exception.html', heading='Error')

class Error(): pass

@app.route('/')
@app.route('/run/', methods=['GET', 'POST'])
def run():
    if request.method == 'POST':
        if request.form['submit'] == 'Run':
            status['thread'] = 'Running'
        elif request.form['submit'] == 'Stop':
            status['thread'] = 'Stopped'
        else:
            pass # unknown
    return render_template('run.html', heading='Run', state=status, data=brew_recipe)


@app.route('/edit/', methods=['GET', 'POST'])
def edit():
    global brew_recipe
    last_action = 'Empty'
    if request.method == 'POST':
        if request.form['submit'] == 'Add_Row':
            brew_recipe['list'].append((0.0,0))
            last_action = 'Add_Row'
        elif request.form['submit'] == 'Delete_Row':
            brew_recipe['list'].pop(-1)
            last_action = 'Delete_Row'
        elif request.form['submit'] == 'Save':
            eval_edit_form(request.form, brew_recipe)
            recipes.save(brew_recipe)
            last_action = 'Save'
        elif request.form['submit'] == 'Reset':
            brew_recipe = recipes.get_default()
            last_action = 'Reset'
        else:
            pass
    return render_template('edit.html', heading='Edit', data=brew_recipe, last_action=last_action)

@app.route('/manage/', methods=['GET', 'POST'])
def manage():
    global brew_recipe
    if request.method == 'POST':
        eval_manage_form(request.form)
        brew_recipe = recipes.get_selected_recipe()

    selected = recipes.get_selected_fname()
    return render_template('manage.html', heading='Manage', fnames=recipes.fnames, selected=selected)

def eval_edit_form(form, brew_recipe):
    brew_recipe['name'] = form['name']
    tmp_list = []
    i = 0
    while True:
        try:
            temp = float(form['t' + str(i)])
            duration = int(form['d' + str(i)])
            tmp_list.append((temp,duration))
            i += 1
        except:
            break
    brew_recipe['list'] = tmp_list

def eval_manage_form(form):
    i = 0
    while True:
        try:
            if 's' + str(i) in form:
                # Select entry
                recipes.select(i)
                break
            if 'd' + str(i) in form:
                # Delete entry
                recipes.delete(i)
                break
            i += 1
        except:
            break


if __name__ == '__main__':
    #app.debug = True
    app.run(host='192.168.178.81')
