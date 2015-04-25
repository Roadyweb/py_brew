#!/usr/bin/env python
'''
Created on 10.07.2012
@author: baumanst

Main functions to create the webpages
'''


from flask import Flask, request, render_template, flash

import copy
import cook
import datalogger
import wq

from recipes import Recipes

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.secret_key = 'some_secret'

global wqt_thread

pct_thread = cook.ProcControlThread(cook.pct_state_cb)
pct_thread.start()
tmt_thread = cook.TempMonThread(cook.tmt_state_cb)
tmt_thread.start()
wqt_thread = wq.WorkQueueThread(cook.wqt_state_cb)
wqt_thread.start()
wq.wqt_thread = wqt_thread
dlt_thread = datalogger.DataLoggerThread(cook.status, cook.dlt_state_cb)
dlt_thread.start()

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
    global pct_thread
    if not pct_thread or not pct_thread.is_alive():
        raise RuntimeError('ProcControlThread is not running')
    if request.method == 'POST':
        if request.form['submit'] == 'Start':
            pct_thread.start_cooking(brew_recipe)
            dlt_thread.start_logging()
        elif request.form['submit'] == 'Stop':
            pct_thread.stop_cooking()
            dlt_thread.stop_logging()
        else:
            pass # unknown
    return render_template('run.html', heading='Run', state=cook.status, data=brew_recipe)


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

@app.route('/graph/')
def graph():
    return render_template('graph.html', heading='Graph', data=dlt_thread.get_data())

def eval_edit_form(form, brew_recipe):
    brew_recipe['name'] = form['name']
    brew_recipe['method'] = form['method']
    brew_recipe['tempk1'] = float(form['tk1'])
    brew_recipe['durak1'] = int(form['dk1'])
    tmp_list = []
    i = 0
    while True:
        try:
            temp = float(form['t' + str(i)])
            duration = int(form['d' + str(i)])
            tmp_list.append((temp, duration))
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
    app.run(host='192.168.178.80')
