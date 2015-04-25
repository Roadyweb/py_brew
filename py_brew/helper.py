'''
Created on Apr 18, 2015

@author: stefan
'''

import datetime

def timedelta2sec(td):
    # total_seconds is not available in Python 2.6
    #seconds = td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def str_timestamp_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')