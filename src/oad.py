#!/usr/bin/python

# oad.py
# OAuth Detector main file
# Oct 14, 2014
# root@davejingtian.org
# http://davejingtian.org

import sys
import time
import getopt
from WebDBEntry import WebDBEntry
from UrlDB import UrlDB
from OadUtils import OadUtils
from Spiderman import spiderman
from Threadman import threadman

# Use UTF-8 encoding
reload(sys) 
sys.setdefaultencoding('utf-8') 

# Global vars
oad_version = "0.8"

# Available oad hack options recording
# hsp - hack 4 start print
# hus - hack 4 urllib2 stepping
# htr - hack 4 timed run

def showHelp():
	'''
	Show help
	'''
	global oad_version
	print('OAuth Detector (oad) - version %s' %(oad_version))
	print('Usage: oad -d 5 -f web.txt')
	print('-d: searching depth, default 2')
	print('-s: stop at the first match, default False')
	print('-f: web link file')
	print('-j: support JavaScript, default False (needs webdriver)')
	print('-v: debug mode')
	print('-m: enable multi-thread, default False')
	print('-n: number of threads, default 10')
	print('-w: choose certain selenium webdriver - [firefox|chrome|phantomjs]')
	print('-e: early print - print out the findings during running, default False')
	print('-k: oad hacking - pass a string of hacking options - [X,Y,...], dev-use only')
	print('-h: help')

def isWebDriverSupported(w):
	'''
	Check if the web driver is supported
	'''
	if w in ['firefox', 'chrome', 'phantomjs']:
		return True
	else:
		return False

def main():
        '''
        Main method
        '''
	# Configurations
	oad_debug = False
	oad_utils = None
	oad_depth = 2
	oad_file = ''
	oad_js = False
	oad_firstStop = False
	oad_multiThread = False
	oad_numOfThreads = 10
	oad_webdriver = ''
	oad_earlyPrint = False
	oad_hackString = ''

	# Process arguments
	try:
		opts,args = getopt.getopt(sys.argv[1:], "d:f:vhjsmn:w:ek:", []);
		for opt,arg in opts:
			if opt == "-h":
				showHelp()
				sys.exit(1)
			elif opt == "-d":
				oad_depth = int(arg)
			elif opt == "-f":
				oad_file = arg
			elif opt == "-v":
				oad_debug = True
			elif opt == "-j":
				oad_js = True
			elif opt == "-s":
				oad_firstStop = True
			elif opt == "-m":
				oad_multiThread = True
			elif opt == "-n":
				oad_numOfThreads = int(arg)
			elif opt == "-w":
				if isWebDriverSupported(arg):
					oad_webdriver = arg
				else:
					print('Error: unsupported web driver [%s]' %(arg))
					showHelp()
					sys.exit(1)
			elif opt == "-e":
				oad_earlyPrint = True
			elif opt == "-k":
				oad_hackString = arg
			else:
				print('Error: unsupported options (%s, %s)' %(opt, arg))
				showHelp()
				sys.exit(1)

	except getopt.GetoptError:
		print('Error: getopt exception')
		showHelp()
		sys.exit(1)

	# Info 
	print('Info: depth [%d], file [%s]' %(oad_depth, oad_file))
	print('Info: debug [%d], firstStop [%d], JavaScript [%d]' %(oad_debug, oad_firstStop, oad_js))
	print('Info: multiThread [%d], numOfThreads [%d]' %(oad_multiThread, oad_numOfThreads))
	print('Info: webdriver [%s], earlyPrint [%d]' %(oad_webdriver, oad_earlyPrint))
	print('Info: hackString [%s]' %(oad_hackString))

	# Init oad utils
	oad_utils = OadUtils(oad_debug, oad_hackString)

	# Read the file and construct the webDB
	webDB = oad_utils.constructWebDB(oad_file)
	if webDB == []:
		print('Error: constructWebDB failed')
		sys.exit(1)
	print('Info: num of Webs [%d]' %(len(webDB)))

	# Call Spiderman/Threadman for help
	start_time = time.time()
	if not oad_multiThread:
		# Init urlDB
		urlDB = UrlDB(1)
		# Spiderman, Spiderman, do whatever...
		for i in range(len(webDB)):
			web = webDB[i]
			if oad_utils.isHackStartPrintEnabled():
				print('Info: [%s] index [%d] URL [%s] started' %('thread#0', i, web.initUrl))
			spiderman(web, web.initUrl, oad_depth, oad_firstStop, oad_js, oad_debug, oad_utils, 'thread#0', oad_webdriver)
			if oad_earlyPrint:
				print('Info: [%s] index [%d] URL [%s] done' %('thread#0', i, web.initUrl))
				if web.hasOauthUrls():
					web.dump()
					print('-'*20)
			# Only add vulnerable URLs into urlDB
			if web.hasVulnerableOauthUrls():
				urlDB.addUrlWebMapping(web.vulnerableOauthUrls, web.initUrl, 0)
	else:
		# Threadman, Threadman, do whenever...
		tObjs,urlDB = threadman(webDB, oad_numOfThreads, oad_depth, oad_firstStop, oad_js, oad_debug, oad_utils, oad_webdriver, oad_earlyPrint)
		for t in tObjs:
			t.join()
	end_time = time.time()

	# Results
	print('='*20)
	urlDB.generateResults()
	print('='*20)
	oad_utils.generateResults(webDB)

	# Timing
	print('Info: done - core running time [%f] seconds' %(end_time - start_time))



if __name__ == '__main__':
        main()

