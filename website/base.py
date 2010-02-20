# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, os, urllib
import urlparse # используется в getBaseURL()
from xml.sax.saxutils import escape

# GAE imports
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from simplejson.encoder import JSONEncoder

# Local imports
from model import SiteUser
import myxml as xml
import invite

class HTTPException(Exception):
	def __init__(self, code, message):
		self.code = code
		self.message = message

	def __str__(self):
		return '%s(%u): %s' % (type(self).__name__, self.code, self.message)

	def to_xml(self):
		return xml.em(u'message', {'code': self.code, 'text': self.message})

class ForbiddenException(HTTPException):
	def __init__(self):
		HTTPException.__init__(self, 403, u'У вас нет доступа к этой странице.')

class ClosedException(HTTPException):
	def __init__(self, saved=False):
		self.saved = saved
		HTTPException.__init__(self, 403, None)

	def to_xml(self):
		return xml.em(u'closed', { 'saved': self.saved })

class BaseRequestHandler(webapp.RequestHandler):
	pageName = 'base'
	xsltName = 'default.xsl'

	def is_open(self):
		"""
		Возвращает True, если сайт работает в открытом режиме и False,
		если только по приглашениям (анонимные пользователи не допускаются).
		"""
		return False

	def check_access(self, admin=False):
		saved = 'saved' in self.request.arguments()
		if not self.is_open():
			try:
				if admin:
					user = self.force_admin()
				else:
					user = self.force_user()

				luser = invite.store(self, user.email())
				if not luser.invited:
					raise ClosedException(saved)
			except HTTPException:
				raise ClosedException(saved)

	def getBaseURL(self):
		"""
		Возвращает базовый адрес текущего сайта.
		"""
		url = urlparse.urlparse(self.request.url)
		return url[0] + '://' + url[1] + '/'

	def getHost(self):
		url = urlparse.urlparse(self.request.url)
		return url[1]

	def render(self, template_name, vars={}):
		"""
		Вызывает указанный шаблон, возвращает результат.
		"""
		vars['base'] = self.getBaseURL()
		vars['host'] = self.getHost()
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)
		return template.render(path, vars)

	def is_admin(self):
		return users.is_current_user_admin()

	def is_cron(self):
		"""
		Возвращает True, если запрос поступил от планировщика.
		http://code.google.com/intl/ru-RU/appengine/docs/python/config/cron.html
		"""
		return self.is_admin() and 'X-AppEngine-Cron' in self.request.headers and self.request.headers['X-AppEngine-Cron']

	def force_admin(self):
		if not self.is_admin():
			raise HTTPException(403, u'У вас нет доступа к этой странице.')
		return self.force_user()

	def get_current_user(self):
		"""
		Возвращает текущего пользователя (SiteUser), при необходимости создавая объект.
		"""
		luser = self.force_user()
		duser = SiteUser.gql('WHERE user = :1', luser).get()
		if duser is None:
			duser = SiteUser(user=luser, weight=0.5)
			duser.put()
		return duser

	def force_user(self):
		user = users.get_current_user()
		if not user:
			raise HTTPException(401, u'Для доступа к этой странице требуется авторизация.')
		return user

	def force_user_or_admin(self, user):
		u = self.force_user()
		if u != user and not users.is_current_user_admin():
			raise HTTPException(401, u'Для доступа к этой странице требуется авторизация.')
		return u

	def sendXML(self, content, attrs=None):
		if attrs is None:
			attrs = {}
		if users.get_current_user():
			attrs['logout-uri'] = users.create_logout_url(self.request.uri)
		else:
			attrs['login-uri'] = users.create_login_url(self.request.uri)
		if users.is_current_user_admin():
			attrs['is-admin'] = 'yes'
		if users.get_current_user():
			attrs['user'] = users.get_current_user().nickname()
			attrs['email'] = users.get_current_user().email()
		attrs['class'] = type(self).__name__
		attrs['name'] = self.pageName
		attrs['theme'] = self.request.get('theme', 'default')

		result = u"<?xml version=\"1.0\"?>"
		if 'xml' not in self.request.arguments():
			result += u"<?xml-stylesheet type=\"text/xsl\" href=\"/static/themes/" + attrs['theme'] + '/' + self.xsltName + u"\"?>\n"
		result += xml.em(u'page', attrs, content)
		self.response.headers['Content-Type'] = 'application/xml; charset=utf-8'
		self.response.out.write(result)

	def sendText(self, content):
		self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
		self.response.out.write(content)

	def sendJSON(self, content):
		json = JSONEncoder().encode(content)
		self.sendAny('application/json', json)

	def sendAny(self, type, content):
		self.response.headers['Content-Type'] = type + '; charset=utf-8'
		self.response.out.write(content)

	def handle_exception(self, e, debug_mode):
		"""
		Заворачивает сообщения об ошибках в <message>.
		http://code.google.com/intl/ru/appengine/docs/python/tools/webapp/requesthandlerclass.html#RequestHandler_handle_exception
		"""
		logging.warning(e)
		if isinstance(e, HTTPException):
			self.error(e.code)
			self.sendXML(e.to_xml())
		else:
			webapp.RequestHandler.handle_exception(self, e, debug_mode)

	def quote(self, text):
		return urllib.quote(text.encode('utf8'))

	def unquote(self, text):
		return urllib.unquote(text).decode('utf8')

def run(rules):
	_DEBUG = True # ('Development/' in os.environ.get('SERVER_SOFTWARE'))
	if _DEBUG:
		logging.getLogger().setLevel(logging.DEBUG)
	application = webapp.WSGIApplication(rules, debug=_DEBUG)
	wsgiref.handlers.CGIHandler().run(application)
