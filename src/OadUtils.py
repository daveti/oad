# OadUtils.py
# OAuth Detector Utils class file
# NOTE: Do NOT introduce/use any global vars!
# OadUtils should be thread-safe!
# Oct 14, 2014
# root@davejingtian.org
# http://davejingtian.org

import re
import string
from WebDBEntry import WebDBEntry
from BeautifulSoup import BeautifulSoup

class OadUtils:

	debug = False
	hackList = []


	def __init__(self, debug, hacks):
		'''
		Constructor
		'''
		self.debug = debug
		if hacks != '':
			self.hackList = string.split(hacks, ',')

	
	def isHackStartPrintEnabled(self):
		'''
		Check if dumping the URL before spiderman starts to work is enabled
		'''
		for h in self.hackList:
			if h == 'hsp':
				return True
		return False


	def isHackUrllib2StepEnabled(self):
		'''
		Check if dumping the urllib2 calling steps is enabled
		'''
		for h in self.hackList:
			if h == 'hus':
				return True
		return False


	def isHackTimedRunEnabled(self):
		'''
		Check if timed_run is enabled
		'''
		for h in self.hackList:
			if h == 'htr':
				return True
		return False


	def readWebFile(self, filePath):
        	'''
        	Read a web file into a list
        	'''
        	data = []
		try:
                	fnObj = open(filePath, 'r')
                	for line in fnObj:
                        	line = line.strip()
				url = self.fixUrlIfNeeded(line, None)
                        	data.append(url)
		finally:
			fnObj.close()

		return data


	def isOauthUrl(self, url):
		'''
		Determine if this URL is oauth related
		'''
		if self.debug:
			print('Debug: isOauthUrl url [%s]' %(url))

		# Check for OAuth key word
		# OAuth key word is not reliable but a quick match
		if url.find('oauth') != -1:
			return True
		# A more 'official' way to find an OAuth URL
		elif ((url.find('client_id') != -1) and (url.find('response_type') != -1)):
			return True
		else:
			return False


	def isOauthUrlVulnerable(self, url):
		'''
		Determine if this oauth URL is vulnerable
		'''
		if self.debug:
			print('Debug: isOauthUrlVulnerable url [%s]' %(url))

		# Check for 'state' and 'response_type=code'
		if ( ((url.find('state=') == -1) or (url.find('state%3d') == -1)) and ((url.find('response_type=code')) != -1 or (url.find('response_type%3dcode') != -1)) ):
			return True
		else:
			return False


	def isUrlFiltered(self, url):
		'''
		Determine if this URL should be filtered based on suffix
		'''
		if self.debug:
			print('Debug: isUrlFiltered url [%s]' %(url))

		# Construct the quick matching list
		matches = ['html', 'shtml']

		# Matching
		for k in matches:
			if url.endswith(('.'+k)):
				return False

		# Construct the filter
		filters = ['jpg', 'jpeg', 'gif', 'png', 'css', 'ico', 'icon', 'txt', 'doc', 'docx', 'pdf', 'ppt', 'tex', 'tar', 'zip', 'xz', 'gz', 'bz2', 'rar']
		# TODO: what about rss/js/css/php/xml/jsp/asp/aspx...
		# daveti: do we want to filter them?

		# Filtering
		for k in filters:
			if url.endswith(('.'+k)):
				return True

		# Construct the front-end filter
		feFilters = ['ftp', '///', '\\', 'javascript:']
		for k in feFilters:
			if url.startswith(k):
				return True

		# Construct the hardcode filter
		hcFilters = ['/', '//', 'javascript:;', 'http://#', 'https://#', '']
		for k in hcFilters:
			if url == k:
				return True

	def getUrlCore(self, url):
		'''
		Extract the URL core by removing the 'http(s)://' prefix and '/' suffix
		'''
		core = ''
		head1 = 'http://'
		head2 = 'https://'
		end = '/'

		# Remove the prefix
		if url.startswith(head1):
			core = url[len(head1):]
		elif url.startswith(head2):
			core = url[len(head2):]
		else:
			if self.debug:
				print('Debug: getUrlCore unsupported url [%s]' %(url))

		# Remove the suffix
		if url.endswith(end):
			core = core[:-1]

		return core


	def isHttpsRedirect(self, url, newUrl):
		'''
		Determine if newUrl is just the HTTPS/same version of url
		'''
		# Quick match
		if url == newUrl:
			return True

		# Get cores
		urlCore = self.getUrlCore(url)
		newUrlCore = self.getUrlCore(newUrl)
		if urlCore == newUrlCore:
			return True

		return False


	def compressUrls(self, urls, parent0, parent1):
		'''
		Remove the duplicates and parents from the URL list
		'''
		newUrls = list(set(urls))
		if parent0 in newUrls:
			newUrls.remove(parent0)
		if parent1 in newUrls:
			newUrls.remove(parent1)

		return newUrls


	def findParentUrl(self, url):
		'''
		Return the parent URL from the current URL
		'''
		# Reverse the URL
		revUrl = url[::-1]

		# Find the 2nd '/'
		index = revUrl.find('/')
		if index == -1:
			if self.debug:
				print('Debug: findParentUrl failed 1st')
			return url
		index = revUrl.find('/', index+1)
		if index == -1:
			if self.debug:
				print('Debug: findParentUrl failed 2nd')
			return url

		# Chop it
		revUrl = revUrl[index:]

		# Reverse again
		revUrl = revUrl[::-1]
		if self.debug:
			print('Debug: findParentUrl return [%s]' %(revUrl))

		return revUrl


	def fixUrlIfNeeded(self, url, parentUrl):
		'''
		Fix the URL if it is missing http(://) prefix
		'''
		if self.debug:
			print('Debug: fixUrlIfNeeded url [%s], parentUrl [%s]' %(url, parentUrl))

		if ((url.startswith('http://')) or (url.startswith('https://'))):
			return url

		# Fix the URL
		if url.startswith('://'):
			return 'http'+url
		elif url.startswith('//'):
			return 'http:'+url
		elif url.startswith('../'):
			# Parent directory
			parentUrl = self.findParentUrl(parentUrl)
			return parentUrl+url[3:]
		elif url.startswith('./'):
			# Current directory
			if parentUrl.endswith('/'):
				url = url[2:]
			else:
				url = url[1:]
			return parentUrl+url
		elif url.startswith('/'):
			# Assume current directory
			if parentUrl.endswith('/'):
				url = url[1:]
			return parentUrl+url
		else:
			return 'http://'+url


	def getUrlsV1(self, page):
		'''
		Get all URLs from the html source page version 1
		'''
		# Hunt for all 'http://...' or 'https://...'
		# NOTE: any RE could be wrong! That is why html parsing
		# is more preferred. However getUrlsV2() generates less
		# URLs...
		# TODO
		urls = []

		return urls


	def getUrlsV2(self, page):
		'''
		Get all URLs from the html source page version 2
		'''
		# Hunt for <a> tag with 'href' attribute
		urls = []
		try:
			soup = BeautifulSoup(page)
		except TypeError:
			if self.debug:
				print('Debug: TypeError in BeautifulSoup')
			return urls

		aTags = soup.findAll('a')

		for tag in aTags:
			url = tag.get('href', None)
			if url != None:
				urls.append(url)

		return urls


	def constructWebDB(self, f):
		'''
		Construct the Web DB from the web link file
		'''
		webs = []
		webDB = []
		# Read in the webs
		webs = self.readWebFile(f)
		if self.debug:
			print('Debug: num of webs [%d]' %(len(webs)))
			print('Debug: webs:')
			print(webs)

		# Construct the DB
		if webs != []:
			for w in webs:
				webDB.append(WebDBEntry(w, 0))
		else:
			print('Error: empty web link file')

		return webDB


	def generateResults(self, db):
		'''
		Generate the final report
		'''
		numOfUrls = 0
		numOfJSs = 0
		numOfOauthUrls = 0
		numOfVulnerableOauthUrls = 0
		numOfVulnerableWebs = 0

		for w in db:
			numOfUrls += w.numOfUrls
			numOfJSs += w.numOfJSs
			numOfOauthUrls += len(w.oauthUrls)
			numOfVulnerableOauthUrls += len(w.vulnerableOauthUrls)
			if w.hasVulnerableOauthUrls():
				numOfVulnerableWebs += 1

			if self.debug:
				w.dump()
				print('-'*20)
			else:
				# Only dump the vulnerable ones right now
				if w.hasVulnerableOauthUrls():
					w.dump()
					print('-'*20)

		# Print out the final results
		print('oad statistics:')
		print('numOfWebs: %d' %(len(db)))
		print('numOfUrls: %d' %(numOfUrls))
		print('numofJSs: %d' %(numOfJSs))
		print('numOfOauthUrls: %d' %(numOfOauthUrls))
		print('numOfVulnerableOauthUrls: %d' %(numOfVulnerableOauthUrls))
		print('numOfVulnerableWebs: %d' %(numOfVulnerableWebs))
