import os
from os.path import join as pjoin
import errno
from functools import wraps
import time
import atexit

###########################################################
#
# This module provides some helper methods
#
##########################################################

#create global dictionary to store execution times of various methods
from collections import OrderedDict
timelogDict=OrderedDict()

def chronomat(method):
    """
    Method to measure execution time of individual methods.
    Simply add the decorator @chronomat to your method definition to print 
    the methods execution time at the end of the run. Stores values in a global dictionary.
    """
    @wraps(method)
    def timeThis(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        timelogDict[method.__module__+'.'+method.__name__]='%2.2f ms' % ( (te - ts) * 1000)
        return result
    return timeThis

@atexit.register
def chronolog():
	"""
	Print the global runtime dictionary upon termination of the python interpreter.
	"""
	for key, item in timelogDict.items():
		print('%s(): %s' % (key, item)) 	
	
