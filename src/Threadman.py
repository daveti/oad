# Threadman.py
# Thread manager implementation
# Oct 19, 2014
# root@davejingtian.org
# http://davejingtian.org

import threading
from UrlDB import UrlDB
from WebDBEntry import WebDBEntry
from Spiderman import spiderman


def computeNumOfThreads(db, threadNum, debug):
	'''
	Compute the number of threads needed based on DB and number requested
	'''
	if debug:
		print('Debug: computeNumOfThreads params')
		print('len(db) [%d], threadNum [%d]' %(len(db), threadNum))

	if len(db) >= threadNum:
		return threadNum
	else:
		return len(db)


def mapReduceDB(db, threadNum, debug):
	'''
	MapReduce the original DB and return a list of sub DBs
	'''
	if debug:
		print('Debug: mapReduceDB params')
		print('len(db) [%d], threadNum [%d]' %(len(db), threadNum))

	dbList = []
	entryNum = 0
	remain = 0
	if threadNum == len(db):
		# Per web DB entry per thread
		entryNum = 1
	elif threadNum < len(db):
		# Most common case
		entryNum = len(db) / threadNum
		remain = len(db) % threadNum
	else:
		print('Error: threadNum [%d] > len(db) [%d]' %(threadNum, len(db)))
		return dbList

	if debug:
		print('Debug: entryNum [%d], remain [%d]' %(entryNum, remain))

	# Construct sub DBs and dbList
	subDB = []
	for i in range(len(db)-remain):
		subDB.append(db[i])
		if len(subDB) == entryNum:
			dbList.append(subDB)
			subDB = []
	if debug:
		print('Debug: numOfSubDBs [%d]' %(len(dbList)))

	# Load balance the remain
	# Assume subDB num >= remain
	if remain != 0:
		revDB = db[::-1]
		for i in range(remain):
			dbList[i].append(revDB[i])

	# Defensive checking
	total = 0
	for d in dbList:
		total += len(d)
	if total != len(db):
		print('Error: missing web DB entries [%d/%d]' %(total, len(db)))

	return dbList


def worker(db, depth, firstStop, supportJS, debug, utils, tid, driver, earlyPrint, urlDB):
	'''
	Thread worker function
	'''
	if debug:
		print('Debug: worker params')
		print('len(db) [%d], depth [%d], firstStop [%d]' %(len(db), depth, firstStop))
		print('supportJS [%d], debug [%d], tid [%d], driver [%s], earlyPrint [%d]' %(supportJS, debug, tid, driver, earlyPrint))
		print('utils: ', utils)
		print('urlDB: ', urlDB)

	# Call Spiderman for help
	name = 'thread#' + str(tid)
	for i in range(len(db)):
		w = db[i]
		if utils.isHackStartPrintEnabled():
			print('Info: [%s] index [%d] URL [%s] started' %(name, i, w.initUrl))
		spiderman(w, w.initUrl, depth, firstStop, supportJS, debug, utils, name, driver)
		if earlyPrint:
			print('Info: [%s] index [%d] URL [%s] done' %(name, i, w.initUrl))
			if w.hasOauthUrls():
				w.dump()
				print('-'*20)
		# Only add vulnerable URLs into urlDB
		if w.hasVulnerableOauthUrls():
			urlDB.addUrlWebMapping(w.vulnerableOauthUrls, w.initUrl, tid)

	# Hack
	#print('Hack: [%s] worker done' %(name))


def threadman(db, threadNum, depth, firstStop, supportJS, debug, utils, driver, earlyPrint):
	'''
	Main function to create multi threads
	'''
	if debug:
		print('Debug: threadman params')
		print('len(db) [%d], threadNum [%d], depth [%d]' %(len(db), threadNum, depth))
		print('firstStop [%d], supportJS [%d], debug [%d], driver [%s], earlyPrint [%d]' %(firstStop, supportJS, debug, driver, earlyPrint))
		print('utils: ', utils)

	# Compute the number of threads needed
	numOfThreads = computeNumOfThreads(db, threadNum, debug)
	if debug:
		print('Debug: numOfThreads [%d]' %(numOfThreads))

	# MapReduce the original DB
	subDBs = mapReduceDB(db, numOfThreads, debug)
	if debug:
		print('Debug: numOfSubDBs [%d]' %(len(subDBs)))

	# Alloc the urlDB based on thread#
	urlDB = UrlDB(len(subDBs))

	# Threading
	threadObjs = []
	for i in range(len(subDBs)):
		# Construct the thread name
		t_name = 'thread#' + str(i)
		# Construct the target args
		t_args = (subDBs[i], depth, firstStop, supportJS, debug, utils, i, driver, earlyPrint, urlDB)
		# Let us rock!
		t = threading.Thread(target=worker, name=t_name, args=t_args)
		# Append at first
		threadObjs.append(t)

	# Start
	for t in threadObjs:
		t.start()
		if debug:
			print('Debug: [%s] started' %(t_name))

	return (threadObjs, urlDB)


