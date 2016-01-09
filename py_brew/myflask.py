#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 10.07.2012
@author: baumanst

Main functions to create the webpages
'''


from flask import Flask, request, render_template
import flask_socketio
import datetime
import time

import config
import cook
import datalogger
import signal
import wq

from recipes import Recipes

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.secret_key = 'some_secret'
socketio = flask_socketio.SocketIO(app)

global wqt_thread

tpc = cook.TempProcessControl(cook.cook_state_cb, cook.cook_temp_state_cb)
pct_thread = cook.ProcControlThread(cook.pct_state_cb, cook.pct_get_state_cb, tpc)
pct_thread.start()
tmt_thread = cook.TempMonThread(cook.tmt_state_cb)
tmt_thread.start()
wqt_thread = wq.WorkQueueThread(cook.wqt_state_cb)
wqt_thread.start()
wq.wqt_thread = wqt_thread
dlt_thread = datalogger.DataLoggerThread(cook.status, cook.dlt_state_cb)
dlt_thread.start()
bm = wq.BlubberManager(cook.bm_state_cb)
wq.bm = bm
smt_thread = datalogger.SocketMessageThread(cook.status, socketio)
smt_thread.start()

last_action = 'Leer'
default_str_time = '07:00'

recipes = Recipes()
brew_recipe = recipes.get_default()


def stop_all_threads():
    threads = [pct_thread, tmt_thread, wqt_thread, dlt_thread, smt_thread]
    for thread in threads:
        if thread.is_alive():
            print thread.name + ' is still alive'
        thread.exit()
        while thread.is_alive():
            time.sleep(0.1)


def handler(signum, frame):
    print 'Signal handler called with signal', signum
    stop_all_threads()

# Register signal handler that stopps all threads
# signal.SIGTERM is issued from supervisor
signal.signal(signal.SIGTERM, handler)


@app.errorhandler(IOError)
def special_exception_handler(error):
    return render_template('exception.html', heading='Error')


class Error(): pass


@app.route('/', methods=['GET', 'POST'])
@app.route('/run/', methods=['GET', 'POST'])
def run():
    global pct_thread
    global default_str_time
    # if not pct_thread or not pct_thread.is_alive():
    #    raise RuntimeError('ProcControlThread is not running')
    if request.method == 'POST':
        print request.form
        if 'btn_start' in request.form:
            pct_thread.start_cooking(brew_recipe)
            dlt_thread.start_logging()
        elif 'btn_start_at' in request.form:
            # Calculate datetime object when cooking should start
            str_time = request.form['start_time']
            default_str_time = str_time
            start_at_hour = int(str_time.split(':')[0])
            start_at_min = int(str_time.split(':')[1])
            now = datetime.datetime.now()
            start_at = datetime.datetime.now().replace(hour=start_at_hour,
                                                       minute=start_at_min,
                                                       second=0,
                                                       microsecond=0)
            # Add a day when start_at is in the past
            if now > start_at:
                start_at += datetime.timedelta(days=1)
            print now, start_at
            pct_thread.start_cooking(brew_recipe, start_at)
            dlt_thread.start_logging()
        elif 'btn_stop' in request.form:
            pct_thread.stop_cooking()
            dlt_thread.stop_logging()
        elif 'btn_t1_up' in request.form:
            tpc.inc_offset(0.2)
        elif 'btn_t1_down' in request.form:
            tpc.inc_offset(-0.2)
        else:
            pass # unknown
    # When cooking is started always use the recipe that is currently running
    if cook.status['pct_state'] == 'Waiting' or \
       cook.status['pct_state'] == 'Running':
        cur_recipe = cook.status['recipe']
    else:
        cur_recipe = brew_recipe
    return render_template('run.html', heading='Run', start_at=default_str_time,
                           state=cook.status, data=cur_recipe)


@app.route('/edit/', methods=['GET', 'POST'])
def edit():
    global brew_recipe
    last_action = 'Empty'
    if request.method == 'POST':
        print request.form
        if 'btn_add_row' in request.form:
            brew_recipe['list'].append((0.0,0))
            last_action = 'Zeile hinzu'
        elif 'btn_del_row' in request.form:
            brew_recipe['list'].pop(-1)
            last_action = u'Zeile löschen'
        elif 'btn_save' in request.form:
            eval_edit_form(request.form, brew_recipe)
            recipes.save(brew_recipe)
            last_action = 'Speichern'
        elif 'btn_reset' in request.form:
            brew_recipe = recipes.get_default()
            last_action = u'Zurücksetzen'
        else:
            pass
    return render_template('edit.html',
                           heading='Edit',
                           data=brew_recipe,
                           last_action=last_action)


@app.route('/manage/', methods=['GET', 'POST'])
def manage():
    global brew_recipe
    if request.method == 'POST':
        eval_manage_form(request.form)
        brew_recipe = recipes.get_selected_recipe()

    selected = recipes.get_selected_fname()
    return render_template('manage.html',
                           heading='Manage',
                           fnames=recipes.fnames,
                           selected=selected)


@app.route('/graph/', methods=['GET', 'POST'])
def graph():
    if request.method == 'POST':
        if 'btn_reset_graph' in request.form:
            dlt_thread.reset_data()
    return render_template('graph.html',
                           heading='Graph',
                           data=dlt_thread.get_data(),
                           state=cook.status)


@app.route('/table/')
def table():
    return render_template('table.html',
                           heading='Table',
                           data=dlt_thread.get_data())


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


@socketio.on('connect')
def test_connect():
    print('Server: Someone connected. Emitting ')
    # socketio.send('Response to connect')
    # socketio.emit('my response', {'data': 'Connected'})


@socketio.on('disconnect')
def test_disconnect():
    print('Server: Someone disconnected')
    # socketio.emit('my response', {'data': 'Connected'})


@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)


@socketio.on('my event')
def handle_my_custom_event(json):
    print('my_event - received json: ' + str(json))


@socketio.on_error()        # Handles the default namespace
def error_handler(e):
    print e


if __name__ == '__main__':
    try:
        app.debug = config.FLASK_DEBUG
        socketio.run(app, host=config.IP_ADDRESS)
    except KeyboardInterrupt:
        socketio.stop()

    stop_all_threads()
