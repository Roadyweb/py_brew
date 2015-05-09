'''
Created on Apr 12, 2015

@author: stefan
'''

import cook
import re
import os
import time

def tempk1():
    return read_sensor('/sys/bus/w1/devices/28-03146cb103ff/w1_slave')

def tempk2():
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
            print value
        f.close()
    except (IOError), e:
        print time.strftime("%x %X"), "Error reading", path, ": ", e
    return value

def pump1(state):
    #os.system('gpio -g mode 22 out')
    if state == '0':
        #os.system('gpio -g write 22 0')
        pass
    else:
        #os.system('gpio -g write 22 1')
        pass
    cook.status['pump1'] = state

def pump2(state):
    cook.status['pump2'] = state

def heater(state):
    cook.status['heater'] = state

if __name__ == '__main__':
    pass