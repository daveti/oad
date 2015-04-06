# WebDBEntry.py
# Web DB entry class file
# Oct 14, 2014
# root@davejingtian.org
# http://davejingtian.org

class WebDBEntry:

	# If webDB entry is used for intermediate processing,
	# depth is useful for more information.
	depth = 0
	# Initial URL
	initUrl = ''
	# Number of URLs processed
	numOfUrls = 0
	# Number of JavaScripts processed
	numOfJSs = 0
	# OAuth URLs found
	oauthUrls = []
	# Vulnerable OAuth URLs found
	vulnerableOauthUrls = []


	def __init__(self, url, depth):
		'''
		Constructor
		'''
		self.initUrl = url
		self.depth = depth
		# Make sure each obj has its own list mem
		self.oauthUrls = []
		self.vulnerableOauthUrls = []


	def hasOauthUrls(self):
		'''
		Determine if there is any OAuth URL used by this web site
		'''
		if len(self.oauthUrls) != 0:
			return True
		else:
			return False


	def hasVulnerableOauthUrls(self):
		'''
		Determine if there is any vulnerable OAuth URL used by this web site
		'''
		if len(self.vulnerableOauthUrls) != 0:
			return True
		else:
			return False


	def dump(self):
		'''
		Dump the current entry
		'''
		print('depth [%d], numOfUrls [%d], numOfJSs [%d]' %(self.depth, self.numOfUrls, self.numOfJSs))
		print('InitURL [%s]' %(self.initUrl))
		print('OAuth URLs:')
		print(self.oauthUrls)
		print('Vulnerable OAuth URLs:')
		print(self.vulnerableOauthUrls)


