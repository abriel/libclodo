import httplib
from simplejson import JSONDecoder


class APIClodo():

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
		self.__auth_token = response.getheader('X-Auth-Token')
		self.__management_url = response.getheader('X-Server-Management-Url')

	def __request(self, method, uri):
		htcs = httplib.HTTPSConnection( httplib.urlsplit(self.__management_url).netloc )
		htcs.putrequest(method, httplib.urlsplit(self.__management_url).path + uri)
		htcs.putheader('X-Auth-Token', self.__auth_token)
		htcs.putheader('Accept', 'application/json')
		htcs.endheaders()

		response = htcs.getresponse()
		json_data = response.read()
		
		return JSONDecoder().decode(json_data)

	def get_account_balance(self):
		answer_record = self.__request('GET', '/billing/balance')

		return answer_record.get('balance')

	def get_server_status(self, server_id):
		answer_record = self.__request('GET', '/servers/' + server_id.__str__())

		return answer_record.get('server').get('status')

