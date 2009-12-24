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

class ForbiddenException(Exception): pass

class UnauthorizedException(Exception): pass

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
		if not users.get_current_user():
			raise UnauthorizedException()

	def formatXML(self, message, *args, **kw):
		xml = u'<' + message
		for (k) in kw:
			value = kw[k]
			if value:
				if type(value) == type(str()) or type(value) == type(unicode()):
					value = escape(value)
				xml += u' ' + k + '="' + value + '"'
		xml += u'/>'
		return xml

	def mkem(self, name, dict):
		xml = u'<' + name
		for k in dict:
			if dict[k]:
				xml += u' ' + k + u'="' + escape(unicode(dict[k])) + u'"'
		xml += u'/>'
		return xml

	def sendXML(self, xml):
		result = "<?xml version=\"1.0\"?>"
		result += "<?xml-stylesheet type=\"text/xsl\" href=\"/static/style.xsl\"?>\n"
		if users.get_current_user():
			result += '<page logout-uri="%s">' % escape(users.create_logout_url(self.request.uri))
		else:
			result += '<page login-uri="%s">' % escape(users.create_login_url(self.request.uri))
		result += xml + '</page>'
		self.response.headers['Content-Type'] = 'application/xml; charset=utf-8'
		self.response.out.write(result)

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
