# TimedRun.py
# Timeout any function call in Python using threading
# Reference: https://meitham.com/2012/12/15/timeout-a-python-callable/
# Nov 11, 2014
# root@davejingtian.org
# http://davejingtian.org

from datetime import datetime
import sys
import threading
import time

class TimeoutError(Exception):
	"""
	Shall be raised when exceeding allowed time limit
	"""


def timed_run(func, args=(), kwargs={}, timeout=None):
	"""
	Runs a function ``func`` and returns a result or raising TimeoutError if
	function does not complete within provided timeout, when timeout is not none.
	WARNING: This won't work on functions that don't release the GIL or don't
	return to the ceval loop.
	>>> def f(x=1):
	...     time.sleep(5)
	...     return x/1
	>>> timed_run(f)  # should not timeout
	1
	>>> timed_run(f, timeout=2)  # should timeout
	Traceback (most recent call last):
	...
	RuntimeError: Thread aborted as requested.
	>>> def g(x=None):
	...     print('hello')
	...     f(None)
	>>> timed_run(g)  # should raise exception
	Traceback (most recent call last):
	...
	TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'
	"""
	class TimedThread(threading.Thread):
		"""
		An abortable thread, by merly raising an exception inside its context
		"""
		def __init__(self):
			super(TimedThread, self).__init__()
			self.exc_info = (None, None, None)

		def run(self):
			self.started_at = datetime.now()
			try:
				self.result = func(*args, **kwargs)
			except:
				# save the exception as an object attribute
				self.exc_info = sys.exc_info()
				self.result = None
			self.ended_at = datetime.now()

		def abort(self):
			self.ended_at = datetime.now()
			raise RuntimeError("Thread aborted as requested.")

	t = TimedThread()
	t.start()
	t.join(timeout)
	if t.exc_info[0] is not None:  # if there were any exceptions
		t, v, tb = t.exc_info
		raise t, v, tb  # Raise the exception/traceback inside the caller
	if t.is_alive():
		t.abort()
		diff = t.ended_at - t.started_at
		raise RuntimeError("%(f)s timed out after %(d)r seconds" %
			{'f': func, 'd': diff.seconds})
	return t.result

