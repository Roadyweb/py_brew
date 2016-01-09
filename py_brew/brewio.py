'''
Created on Apr 12, 2015

@author: stefan
'''

import random
import re
import os
import time

import config
import cook


def tempk1():
    status = cook.status
    if config.SIMULATION:
        return sim_new_temp(status['tempk1'], status['heater'])
    return read_sensor('/sys/bus/w1/devices/28-041501b1e6ff/w1_slave')

def tempk2():
    status = cook.status
    if config.SIMULATION:
        return sim_new_temp(status['tempk2'], status['pump2'])
    return read_sensor('/sys/bus/w1/devices/28-031501c640ff/w1_slave')

def read_sensor(path):
    ''' reads the value from device in the given path
        return a float, the sensor value when successful, -99.0 otherwise
    '''
    try:
        fd = open(path, "r")
        line = fd.readline()
        if re.match(r"([0-9a-fd]{2} ){9}: crc=[0-9a-fd]{2} YES", line):
            line = fd.readline()
            m = re.match(r"([0-9a-fd]{2} ){9}t=([+-]?[0-9]+)", line)
        if m:
            value = float(m.group(2)) / 1000.0
        fd.close()
    except (IOError), e:
        print time.strftime("%x %X"), "Error reading", path, ": ", e
        value = -99.0
    return value

def pump1(state):
    control('pump1', 17, state)

def pump2(state):
    control('pump2', 22, state)

def heater(state):
    control('heater', 23, state)

def control(device_name, gpio, state):
    if state == 0:
        if not config.SIMULATION:
            set_gpio(gpio, 0)
    else:
        if not config.SIMULATION:
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
    cooling = (temp - config.AMBIENT_TEMP) * config.COOLING_FACTOR
    heating = heat * config.HEATING_FACTOR
    noise = (random.random() - 0.5) * config.RANDOM_FACTOR
    temp += noise + heating - cooling
    return temp

if __name__ == '__main__':
    pass
