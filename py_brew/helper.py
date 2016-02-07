'''
Created on Apr 18, 2015

@author: stefan
'''

import datetime
import re
import os
import sys

from numbers import Number
from collections import Set, Mapping, deque


def timedelta2sec(td):
    # total_seconds is not available in Python 2.6
    #seconds = td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def timedelta2min(td):
    minutes, seconds = divmod(timedelta2sec(td), 60)
    return minutes

def str_timestamp_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def grepline(text, search4str):
    for line in text.splitlines():
        if re.search(search4str, line):
            return line
    return None

def log(text):
    str2log = str_timestamp_now() + ' ' + str(text) + '\r\n'
    try:
        cwd = os.getcwd()
        fname = '/var/log/py_brew.log'
        if os.path.isfile(fname):
            filehandle = open(fname, 'a')
        else:
            filehandle = open(fname, 'w')
        filehandle = open(fname, 'a')
        filehandle.write(str2log)
        filehandle.close()
    except:
        sys.stdout.write(str2log)

try: # Python 2
    zero_depth_bases = (basestring, Number, xrange, bytearray)
    iteritems = 'iteritems'
except NameError: # Python 3
    zero_depth_bases = (str, bytes, Number, range, bytearray)
    iteritems = 'items'

def getsize(obj):
    """Recursively iterate to sum size of object & members."""
    def inner(obj, _seen_ids = set()):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, zero_depth_bases):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
        # Now assume custom object instances
        elif hasattr(obj, '__slots__'): 
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        else: 
            attr = getattr(obj, '__dict__', None)
            if attr is not None:
                size += inner(attr)
        return size
    return inner(obj)