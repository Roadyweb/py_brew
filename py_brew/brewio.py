'''
Created on Apr 12, 2015

@author: stefan
'''

import cook

def temp1():
    pass

def temp2():
    pass

def temp3():
    pass

def relais1(state):
    cook.status['relais1'] = state

def relais2(state):
    cook.status['relais2'] = state

def relais3(state):
    cook.status['relais3'] = state

def relais_off():
    relais1(0)
    relais2(0)
    relais3(0)


if __name__ == '__main__':
    pass