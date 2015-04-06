# Spiderman.py
# Core algorithm for oad
# Added Selenium support
# Oct 26, 2014
# TODO: JavaScript support
# Oct 14, 2014
# root@davejingtian.org
# http://davejingtian.org

import sys
import ssl
import socket
import urllib2
import httplib
from selenium import webdriver
from OadUtils import OadUtils
from TimedRun import timed_run
from WebDBEntry import WebDBEntry
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException

# Global vars
spider_urlopen_timeout = 20 # seconds
spider_urlopen_call_timeout = 30 # seconds, should be > urlopen_timeout
webdriver_phantomjs_path = '/home/ethan/phantomjs-1.9.8-linux-x86_64/bin/phantomjs' # path to PhantomJS


def constructWebDriver(debug, driver):
	'''
	Construct the web driver accordingly
	'''
	global spider_urlopen_timeout
	global webdriver_phantomjs_path

	try:
		if driver == 'firefox':
			driver2 = webdriver.Firefox()
		elif driver == 'chrome':
			driver2 = webdriver.Chrome()
		elif driver == 'phantomjs':
			driver2 = webdriver.PhantomJS(webdriver_phantomjs_path)
		else:
			if debug:
				print('Debug: bad web driver [%s]' %(driver))
			return None
	except:
		if debug:
			print('Error: construct webdriver failed ', sys.exc_info()[0])
		return None

	# Set timeout
	try:
		driver2.set_page_load_timeout(spider_urlopen_timeout)
	except:
		if debug:
			print('Error: webdriver set timeout failed ', sys.exc_info()[0])

	return driver2


def spiderJS(root, url, debug, driver):
	'''
	A JS helper used to retrieve all JSs from URL and to
	collect the resulting URLs by running these JSs
	'''
	urls = []

	# Defensive checking
	if debug:
		print('Debug: spiderJS url [%s], driver [%s]' %(url, driver))

	if ((driver == None) or (driver == '')):
		return urls

	if (driver != 'firefox'):
		print('Warning: webdriver [%s] may not return the resultant URL' %(driver))

	# Construct a webdriver
	driver2 = constructWebDriver(debug, driver)
	if driver2 == None:
		print('Error: webdriver open failed')
		return urls

	# Construct a selector list
	selectors = ["a[href^='javascript']", "[onclick]"]

	# Load the URL
	try:
		driver2.get(url)
	except:
		if debug:
			print('Error: webdriver get URL [%s] failed ', sys.exc_info()[0])
		driver2.close()
		return urls


	# Go thru different selectors
	for s in selectors:
		if debug:
			print('Debug: selector [%s]' %(s))

		# Retrieve the JSs and run
		try:
			JSs = driver2.find_elements_by_css_selector(s)
		except:
			if debug:
				print('Error: find css selector failed ', sys.exc_info()[0])
			continue

		num = len(JSs)
		if debug:
			print('Debug: got num of JSs [%d]' %(num))
		# Click each JS
		# NOTE: we can NOT iterate the JSs directly as the
		# click action may redirect the dirver to a new URL,
		# which then cause following JSs failure - not in cache!
		for i in range(num):
			# In case...
			try:
				js = JSs[i]
			except:
				# We should never hit here because of
				# the defensive checking down below for page reloading
				if debug:
					print('Error: exception during indexing ', sys.exc_info()[0])
				break
			# Get some info
			try:
				if debug:
					print('JS text [%s]' %(js.text))
				if selectors.index(s) == 0:
					# Only works for href with JS
					href = js.get_attribute('href')
					script = href[len('javascript:'):]
					if debug:
						print('Debug: script [%s]' %(script))
			except:
				if debug:
					print('Error: exception on getting text/attribute ', sys.exc_info()[0])
				# Just move on
			# Click it
			needToReload = False
			try:
				# Click
				js.click()
			except ElementNotVisibleException:
				if debug:
					print('Error: the web element is not visible - TODO')
			except StaleElementReferenceException:
				if debug:
					print('Error: the web element is stale - relaod the page')
				needToReload = True
			except:
				if debug:
					print('Error: generic exception: ', sys.exc_info()[0])

			# Update the counter
			root.numOfJSs += 1

			# Check for redirect
			driverGoBackFailed = False
			if driver2.current_url != url:
				# Add this new URL
				urls.append(driver2.current_url)
				if debug:
					print('Debug: new URL [%s]' %(driver2.current_url))
				if not needToReload:
					try:
						driver2.back()
					except:
						driverGoBackFailed = True
						if debug:
							print('Error: webdriver going back failed ', sys.exc_info()[0])
					# Recheck
					if (not driverGoBackFailed) and (driver2.current_url != url):
						needToReload = True

			# Reset
			if needToReload or driverGoBackFailed:
				# Reset the driver
				if debug:
					print('Debug: browser reset')
				try:
					driver2.get(url)
				except:
					if debug:
						print('Error: webdriver get URL [%s] failed ', sys.exc_info()[0])
					driver2.close()
					return urls
				try:
					JSs = driver2.find_elements_by_css_selector(s)
				except:
					if debug:
						print('Error: find css selector failed ', sys.exc_info()[0])
					# Try next selector
					break

				# Defensive checking
				if len(JSs) != num:
					if debug:
						print('Error: different number of JSs after reloading (new/old) [%d/%d]' %(len(JSs), num))
					# Try next selector
					break

	# Close the driver
	driver2.close()

	if debug:
		print('Debug: spiderJS got num of URLs [%d]' %(len(urls)))

	return urls


def spiderwoman(root, url, debug, utils):
	'''
	A woman used to help check the URL and update root accordingly
	'''
	# Update the URL counters
	root.numOfUrls += 1

	# Check the URL at the start
	if utils.isOauthUrl(url):
		# NOTE: to save memory, we use URL rather than WebDB entry
		# for intermediate processing (web crawling)!
		# Update the root webDB entry
		root.oauthUrls.append(url)
		if debug:
			print('Debug: found OAuth URL [%s]' %(url))
		# Check if it is vulnerable
		if utils.isOauthUrlVulnerable(url):
			# Update the root webDB entry
			root.vulnerableOauthUrls.append(url)
			if debug:
				print('Debug: found vulnerable OAuth URL [%s]' %(url))
			return True
	return False


def spiderman(root, url, depth, firstStop, supportJS, debug, utils, threadName=None, driver=None):
	'''
	A recurrsive function used to do web crawling
	root: root webDB entry
	url: current URL
	depth: current depth
	firstStop: stop if first match is found
	supportJS: support JavaScript
	debug: debug
	utils: OadUtils instance
	threadName: name of the caller thread
	driver: name of the Selenium webdriver
	'''
	global spider_urlopen_timeout
	global spider_urlopen_call_timeout

	# Debug
	if debug:
		print('Debug: spiderman params')
		print('root:')
		root.dump()
		print('URL: [%s]' %(url))
		print('depth [%d], firstStop [%d], supportJS [%d]' %(depth, firstStop, supportJS))
		print('utils: ', utils)
		print('threadName: [%s], driver [%s]' %(threadName, driver))

	# Base case
	if depth == 0:
		return False

	# Convert it to lower case
	url = url.lower()

	# Call Spiderwoman for help
	if spiderwoman(root, url, debug, utils) and firstStop:
		return True

	# Have to go deeper from the current URL
	# Will check for
	# 1. redirected URL itself
	# 2. URLs from the final source page
	# 3. JSs from the final source page (TODO)
	# NOTE: patial JSs have been processed by Selenium though not all...

	# Hunt for more URLs
	newUrl = ''
	driver2 = None
	urlObj = None
	if ((driver != None) and (driver != '')):
		# Use webdriver
		driver2 = constructWebDriver(debug, driver)
		if driver2 == None:
			print('Error: webdriver open failed')
			return False

		# Load the URL
		try:
			driver2.get(url)
		except:
			if debug:
				print('Error: webdriver loading failed', sys.exc_info()[0])
			driver2.close()
			return False
		# Get the current URL
		newUrl = driver2.current_url
	else:
		# Use urllib2
		try:
			# urllib2 debug
			if utils.isHackUrllib2StepEnabled():
				print('Debug: [%s] starts [urlopen] for URL [%s] with timeout [%d] seconds' %(threadName, url, spider_urlopen_timeout))
			# NOTE: urlopen is evil!
			if utils.isHackTimedRunEnabled():
				urlObj = timed_run(urllib2.urlopen, (url, None, spider_urlopen_timeout), timeout=spider_urlopen_call_timeout)
			else:
				urlObj = urllib2.urlopen(url, timeout=spider_urlopen_timeout)

			if debug:
				print('Debug: [%s-urlopen] for URL [%s]' %(threadName, url))
		except urllib2.HTTPError, e:
			if debug:
				print('Error: [%s-urlopen] HTTPError (%s) for URL [%s]' %(threadName, str(e.code), url))
			return False
		except urllib2.URLError, e:
			if debug:
				print('Error: [%s-urlopen] URLError (%s) for URL [%s]' %(threadName, str(e.reason), url))
			return False
		except httplib.HTTPException, e:
			if debug:
				print('Error: [%s-urlopen] HTTPException for URL [%s]' %(threadName, url))
			return False
		except socket.timeout:
			if debug:
				print('Error: [%s-urlopen] timeout for URL [%s]' %(threadName, url))
			return False
		except RuntimeError:
			if debug:
				print('Error: [%s-urlopen] timed_run timeout for URL [%s]' %(threadName, url))
			return False
		except Exception:
			if debug:
				print('Error: [%s-urlopen] generic exception for URL [%s]:' %(threadName, url))
				print(sys.exc_info()[0])
			return False
		except:
			if debug:
				print('Error: [%s-urlopen] something wrong for URL [%s]' %(threadName, url))
			return False

		# Get the current URL
		newUrl = urlObj.geturl()
		if utils.isHackUrllib2StepEnabled():
			print('Debug: [%s] ends [geturl] with new URL [%s]' %(threadName, newUrl))

	# Check the current URL
	newUrl = newUrl.lower()
	if newUrl == "about:blank":
		# webdriver/urllib2 failed
		if debug:
			print('Debug: webdriver/urllib2 open URL failed [%s]' %(newUrl))
		if urlObj != None:
			urlObj.close()
		return False
	elif not utils.isHttpsRedirect(url, newUrl):
		# A redirected URL:
		# Call Spiderwoman for help
		if debug:
			print('Debug: redirect [%s] -> [%s]' %(url, newUrl))
		if spiderwoman(root, newUrl, debug, utils) and firstStop:
			if urlObj != None:
				urlObj.close()
			return True
	else:
		if debug:
			print('Debug: HTTPS/Same redirect [%s] -> [%s]' %(url, newUrl))

	# Retrieve more URLs
	urls = []
	html = ''
	urlReady = True
	if ((driver != None) and (driver != '') and (driver2 != None)):
		# Use webdriver
		# With Javascript partially supported
		try:
			elems = driver2.find_elements_by_tag_name('a')
		except:
			urlReady = False
			if debug:
				print('Error: find links failed ', sys.exc_info()[0])
			driver2.close()
			return False

		# Retrieve the URLs
		if urlReady:
			for e in elems:
				try:
					href = e.get_attribute('href')
				except:
					if debug:
						print('Error: retrieve URL failed ', sys.exc_info()[0])
					continue
				# Add this URL
				if href != None:
					urls.append(href)
		# Close the driver
		driver2.close()
	else:
		# Use urllib2+beautifulSoup
		# Get the HTML source
		try:
			# urllib2 debug
			if utils.isHackUrllib2StepEnabled():
				print('Debug: [%s] starts [(url)read]' %(threadName))
			html = urlObj.read()
		except ssl.SSLError:
			if debug:
				print('Error: URL read failed - SSL error')
			# Ignore the JS support
			urlObj.close()
			return False
		except:
			if debug:
				print('Error: URL read failed ', sys.exc_info()[0])
			# Ignore the JS support
			urlObj.close()
			return False

		# NOTE: check OadUtils.getUrlsV1/2 for difference
		urls = utils.getUrlsV2(html)
		urlObj.close()

	# Hunt for more URLs from JSs
	if supportJS:
		urls += spiderJS(root, url, debug, driver)

	# Remove the duplicates and the parent URL
	urls = utils.compressUrls(urls, url, newUrl)

	# Debug:
	if debug:
		print('Debug: got [%d] URLs from [%s]' %(len(urls), url))

	# Go thru all the URLs
	if urls != []:
		for u in urls:
			# Convert it at first
			u = u.lower()

			# Do filter at first
			if utils.isUrlFiltered(u):
				if debug:
					print('Debug: filtered URL [%s]' %(u))
				root.numOfUrls += 1
				continue

			# Fix the URL if it is missing http prefix
			# Use the final redirected URL as the parent
			u = utils.fixUrlIfNeeded(u, newUrl)
			if debug:
				print('Debug: fixed URL [%s]' %(u))

			# NOTE: we probably should exclude the URLs which
			# have been checked. However, this requires huge memory
			# and a quick search (hashing) for the matching. Thus,
			# we just K.I.S.S here:)
			if spiderman(root, u, depth-1, firstStop, supportJS, debug, utils, threadName, driver) and firstStop:
				return True
	else:
		if debug:
			print('Debug: no more URLs')
		return False

	return False
