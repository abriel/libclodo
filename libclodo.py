# coding : utf8

import httplib
import datetime
import os

try:
    from json import JSONDecoder, JSONEncoder
except ImportError:
    from simplejson import JSONDecoder # for python < v2.6


class APIClodo(object):

	__access_key     = ''
	__login          = ''
	__auth_token     = ''
	__management_url = ''


	def __init__(self, login, access_key):
		self.__access_key = access_key
		self.__login = login

		self.__get_auth_token()

	def __get_auth_token(self):
		if self.__access_key == '' or self.__login == '' :
			return ''

		httpc = httplib.HTTPConnection('api.clodo.ru')
		httpc.putrequest('GET', '/')
		httpc.putheader('X-Auth-User', self.__login)
		httpc.putheader('X-Auth-Key',  self.__access_key)
		httpc.endheaders()

		response = httpc.getresponse()

		if response.status != 204:
			if response.status == 401:
				raise ClodoAuthorizationFailed()
			else:
				raise ClodoGenericException(code=response.status)

		self.__auth_token = response.getheader('X-Auth-Token')
		self.__management_url = response.getheader('X-Server-Management-Url')

	def __really_request(self, method, uri, body):
		htcs = httplib.HTTPSConnection( httplib.urlsplit(self.__management_url).netloc )
		headers = {
					'Accept' : 'application/json',
					'X-Auth-Token' : self.__auth_token,
					'Content-Type' : 'application/json',
				}
		htcs.request(method, httplib.urlsplit(self.__management_url).path + uri, body, headers)

		return htcs.getresponse()

	def __request(self, method, uri, body=None):
		response = self.__really_request(method, uri, body)

		if response.status == 401:
			self.__get_auth_token()
			response = self.__really_request(method, uri, body)

		json_data = response.read()
		try:
			r_data = JSONDecoder().decode(json_data)
		except ValueError:
			r_data = None

		if response.status not in [200, 204]:
			try:
				os.sys.stderr.write('''Bad request details: 
	METHOD: %s
	URI: %s
	DETAIL: %s
	STATUS CODE: %s
	BODY: %s

	''' % (method, uri, r_data['BadRequest']['details'], response.status, body)
	)
				os.sys.stderr.flush()
			except:
				pass
			raise ClodoGenericException(code=response.status)
		
		return r_data

	def get_account_balance(self):
		try:
			answer_record = self.__request('GET', '/billing/balance')
		except ClodoGenericException as e:
			if e.code == 404:
				raise ClodoRecordsNotFound()
			else:
				raise ClodoGenericException(code=e.code)

		return answer_record.get('balance')

	def get_server_info(self, server_id):
		try:
			answer_record = self.__request('GET', '/servers/' + server_id.__str__())
		except ClodoGenericException as e:
			if e.code == 404:
				raise ClodoServerNotFound()
			else:
				raise ClodoGenericException(code=e.code)

		return answer_record.get('server')

	def get_server_status(self, server_id):
		server_info = self.get_server_info(server_id)

		return server_info.get('status')

	def get_backup_list(self, server_id):
		request = '/servers/' + server_id.__str__() + '/backup/getlist'
		try:
			answer_record = self.__request('GET', request)
		except ClodoGenericException as e:
			if e.code == 404:
				raise ClodoServerNotFound()
			elif e.code == 400:
				raise ClodoRequestError(request)
			else:
				raise ClodoGenericException(code=e.code)
			
		backup_list = answer_record.get('backups').get('backup')
		if isinstance(backup_list, dict):
			backup_list = [backup_list]
		
		return backup_list

	def set_memory_min(self, server, memory_value):
		request_body = {'server':{
			'vps_memory' : memory_value
		}}

		try:
			answer_record = self.__request('PUT', '/servers/%s' % str(server), JSONEncoder().encode(request_body) )
		except ClodoGenericException as e:
			if e.code == 400:
				raise ClodoRequestError('set memory minimal limit')
			elif e.code == 405:
				raise ClodoGenericException(405, 'function temporary not avaliable')
			elif e.code == 500:
				raise ClodoGenericException(500, 'Internal error')
			else:
				raise ClodoGenericException(code=e.code)
		
		return answer_record

	def get_stats(self, server, time_from, time_to='NOW'):
		if time_to == 'NOW':
			time_to = datetime.datetime.now().strftime('%Y-%m-%d %T')
		request_body = {'stats':{
			'from' : time_from,
			'to' : time_to,
		}}

		try:
			answer_record = self.__request('POST', '/stats/%s' % str(server), JSONEncoder().encode(request_body) )
		except ClodoGenericException as e:
			if e.code == 400:
				raise ClodoRequestError('Incorrect Request')
			elif e.code == 404:
				raise ClodoRecordsNotFound()
			else:
				raise ClodoGenericException(code=e.code)
		
		return answer_record['stats']

	def get_stats_traffic(self, server, time_from, time_to=None):
		stats = self.get_stats(server, time_from, time_to) if time_to is not None else self.get_stats(server, time_from)
		if isinstance(stats, dict):
			net_tx = net_rx = 0
			for item in stats['row']:
				net_tx += int(item['net_tx'])
				net_rx += int(item['net_rx'])
			
			return {'net_tx' : net_tx, 'net_rx' : net_rx}
		return None


class ClodoGenericException(Exception):
	
	def __init__(self, code, msg='Unknown error'):
		self.msg = msg
		self.code = code
	
	def __str__(self):
		return repr("%s. Clodo error code: %s" % (self.msg, self.code) )

class ClodoAuthorizationFailed(ClodoGenericException):
	def __init__(self):
		self.msg = 'Authorization error: Can not get X-Auth-Token for given pair LOGIN and ACCESS_KEY'
		self.code = 401

class ClodoGenericNotFound(ClodoGenericException):
	code = 404
	def __init__(self):
		self.msg = 'Generic not found error'

class ClodoRecordsNotFound(ClodoGenericNotFound):
	def __init__(self):
		self.msg = 'No Records Found'

class ClodoServerNotFound(ClodoGenericNotFound):
	def __init__(self):
		self.msg = 'No Servers Found'

class ClodoRequestNotFound(ClodoGenericNotFound):
	def __init__(self):
		self.msg = 'Request not found'

class ClodoRequestError(ClodoGenericException):
	def __init__(self, request):
		self.msg = 'Request (%s) error' % request
		self.code = 400

