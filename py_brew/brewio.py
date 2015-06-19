'''
Created on Apr 12, 2015

@author: stefan
'''

import random
import re
import os
import time

import cook


# Variables for simulation
SIMULATION = True
AMBIENT_TEMP = 10.0     # minimum temperature when no heating is applied
COOLING_FACTOR = 0.005  # cooling in degrees = (curr temp - AMBIENT_TEMP) / COOLING_FACTOR
HEATING_FACTOR = 0.4    # Normal heating is 1 K per second


def tempk1():
    status = cook.status
    if SIMULATION:
        return sim_new_temp(status['tempk1'], status['pump1'])
    return read_sensor('/sys/bus/w1/devices/28-03146cb103ff/w1_slave')

def tempk2():
    status = cook.status
    if SIMULATION:
        return sim_new_temp(status['tempk2'], status['pump2'])
    return read_sensor('/sys/bus/w1/devices/28-031501c640ff/w1_slave')

def read_sensor(path):
    value = "U"
    try:
        f = open(path, "r")
        line = f.readline()
        if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
            line = f.readline()
            m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
        if m:
            value = float(m.group(2)) / 1000.0
            #print value
        f.close()
    except (IOError), e:
        print time.strftime("%x %X"), "Error reading", path, ": ", e
    return value

def pump1(state):
    control('pump1', 17, state)

def pump2(state):
    control('pump2', 22, state)

def heater(state):
    control('heater', 23, state)

def control(device_name, gpio, state):
    if state == 0:
        if not SIMULATION:
            set_gpio(gpio, 0)
    else:
        if not SIMULATION:
            set_gpio(gpio, 1)
    print '%s %d' % (device_name, state)
    cook.status[device_name] = state

def set_gpio(number, state):
    ''' number: gpio number
        state: 0 or 1
    '''
    os.system('gpio -g mode %d out' % number)
    os.system('gpio -g write %d %d' % (number, state))

def sim_new_temp(temp, heat):
    """ Simulates the next temperature """
    cooling = (temp - AMBIENT_TEMP) * COOLING_FACTOR
    heating = heat * HEATING_FACTOR
    noise = (random.random() - 0.5) / 2
    temp += noise + heating - cooling
    return temp

if __name__ == '__main__':
    pass
