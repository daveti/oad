# UrlDB.py
# URL DB class file
# NOTE: we probably do not need this given that
# we could construct this in the fly from WebDB...
# Nov 5, 2014
# root@davejingtian.org
# http://davejingtian.org

class UrlDB:

	# Number of DBs
	numOfDBs = 0
	# All DBs - each DB is a dict
	dbList = []
	# The final summary DB holding URL->[web,...]
	sumDB = {}
	# Number of URLs in sumDB
	numOfUrlsInSum = 0
	# Number of webs in sumDB
	numOfWebsInSum = 0
	# The final summary core DB holding coreURL->[web,...]
	sumCoreDB = {}
	# Number of URLs in sumCoreDB
	numOfUrlsInSumCore = 0
	# Number of webs in sumCoreDB
	numOfWebsInSumCore = 0


	def __init__(self, num):
		'''
		Constructor
		'''
		self.numOfDBs = num
		self.dbList = []
		for i in range(num):
			tmp = {}
			self.dbList.append(tmp)
		self.sumDB = {}
		self.sumCoreDB = {}


	def getUrlCore(self, url):
		'''
		Get the top level domain from the URL
		Different from the one in OadUtils
		'''
		core = ''
		head1 = 'http://'
		head2 = 'https://'
		end = '/'
		idx = -1

		if url.startswith(head1):
			core = url[len(head1):]
		elif url.startswith(head2):
			core = url[len(head2):]
		else:
			core = url[:]

		try:
			idx = core.index(end)
		except:
			idx = -1

		if idx != -1:
			core = core[:idx]

		return core


	def addUrlWebMapping(self, urls, web, idx):
		'''
		Add the URL-Web mapping into the ith DB
		'''
		if idx >= self.numOfDBs:
			print('Error: invalid URL DB index [%d]' %(idx))
			return

		db = self.dbList[idx]
		for u in urls:
			if not db.has_key(u):
				db[u] = []
			db[u].append(web)


	def generateSum(self):
		'''
		Generate the SumDB and SumCoreDB once dbList is filled up
		'''
		for db in self.dbList:
			for k in db.keys():
				# SumDB
				if not self.sumDB.has_key(k):
					self.sumDB[k] = []
				self.sumDB[k] += db[k]
				# SumCoreDB
				core = self.getUrlCore(k)
				if not self.sumCoreDB.has_key(core):
					self.sumCoreDB[core] = []
				self.sumCoreDB[core] += db[k]

		# Remove duplicate values(webs)
		webs = []
		for k in self.sumDB.keys():
			tmp = self.sumDB[k]
			self.sumDB[k] = list(set(tmp))
			webs += self.sumDB[k]
			self.numOfUrlsInSum += 1
		self.numOfWebsInSum = len(set(webs))
		webs = []
		for k in self.sumCoreDB.keys():
			tmp = self.sumCoreDB[k]
			self.sumCoreDB[k] = list(set(tmp))
			webs += self.sumCoreDB[k]
			self.numOfUrlsInSumCore += 1
		self.numOfWebsInSumCore = len(set(webs))

		# Defensive check
		if self.numOfWebsInSum != self.numOfWebsInSumCore:
			print('Error: different num of webs in SumDB and SumCoreDB')


	def dump(self):
		'''
		Dump the summary
		'''
		print('Info: dump SumDB')
		for k in self.sumDB.keys():
			print(k, '->', self.sumDB[k])
		print('Info: numOfUrlsInSum [%d]' %(self.numOfUrlsInSum))
		print('Info: numOfWebsInSum [%d]' %(self.numOfWebsInSum))
		print('-'*20)
		print('Info: dump SumCoreDB')
		for k in self.sumCoreDB.keys():
			print(k, '->', self.sumCoreDB[k])
		print('Info: numOfUrlsInSumCore [%d]' %(self.numOfUrlsInSumCore))
		print('Info: numOfWebsInSumCore [%d]' %(self.numOfWebsInSumCore))


	def generateResults(self):
		'''
		Generate the final results
		'''
		self.generateSum()
		self.dump()

