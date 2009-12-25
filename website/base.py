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

# Local imports
import myxml as xml

class ForbiddenException(Exception):
	def __str__(self):
		return u"У вас нет доступа к этой странице."

class UnauthorizedException(Exception):
	def __str__(self):
		return u"Эта функция доступна только авторизованным пользователям."

class BaseRequestHandler(webapp.RequestHandler):
	def getBaseURL(self):
		"""
		Возвращает базовый адрес текущего сайта.
		"""
		url = urlparse.urlparse(self.request.url)
		return url[0] + '://' + url[1] + '/'

	def render(self, template_name, vars={}, content_type='text/xml'):
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		result = template.render(path, vars)
		self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
		self.response.out.write(result)

	def force_admin(self):
		if not users.is_current_user_admin():
			raise ForbiddenException()
		self.force_user()

	def force_user(self):
		user = users.get_current_user()
		if not user:
			raise UnauthorizedException()
		return user

	def force_user_or_admin(self, user):
		u = self.force_user()
		if u != user and not users.is_current_user_admin():
			raise UnauthorizedException()
		return u

	def sendXML(self, content, attrs={}):
		if users.get_current_user():
			attrs['logout-uri'] = users.create_logout_url(self.request.uri)
		else:
			attrs['login-uri'] = users.create_login_url(self.request.uri)
		if users.is_current_user_admin():
			attrs['is-admin'] = 'yes'
		if users.get_current_user():
			attrs['user'] = users.get_current_user().nickname()

		result = "<?xml version=\"1.0\"?>"
		result += "<?xml-stylesheet type=\"text/xsl\" href=\"/static/style.xsl\"?>\n"
		result += xml.em(u'page', attrs, content)
		self.response.headers['Content-Type'] = 'application/xml; charset=utf-8'
		self.response.out.write(result)

	def handle_exception(self, e, debug_mode):
		"""
		Заворачивает сообщения об ошибках в <message>.
		http://code.google.com/intl/ru/appengine/docs/python/tools/webapp/requesthandlerclass.html#RequestHandler_handle_exception
		"""
		logging.warning(e)
		self.sendXML(xml.em(u'message', {'text': unicode(e)}))

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
