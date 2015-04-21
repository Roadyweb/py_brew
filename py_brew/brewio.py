'''
Created on Apr 12, 2015

@author: stefan
'''

import cook

def temp1():
    pass

def temp2():
    pass

def pump1(state):
    cook.status['pump1'] = state

def pump2(state):
    cook.status['pump2'] = state

def heater(state):
    cook.status['heater'] = state

if __name__ == '__main__':
    pass