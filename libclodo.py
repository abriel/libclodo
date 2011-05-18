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

	def get_account_balance(self):
		htcs = httplib.HTTPSConnection( httplib.urlsplit(self.__management_url).netloc )
		htcs.putrequest('GET', httplib.urlsplit(self.__management_url).path + '/billing/balance')
		htcs.putheader('X-Auth-Token', self.__auth_token)
		htcs.putheader('Accept', 'application/json')
		htcs.endheaders()

		response = htcs.getresponse()
		json_data = response.read()

		balance = JSONDecoder().decode(json_data).get('balance')

		return balance

