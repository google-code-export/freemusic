# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, os, urllib
from xml.sax import saxutils

# GAE imports
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class ForbiddenException(Exception): pass

class UnauthorizedException(Exception): pass

class BaseRequestHandler(webapp.RequestHandler):
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
					value = saxutils.escape(value)
				xml += u' ' + k + '="' + value + '"'
		xml += u'/>'
		return xml

	def sendXML(self, xml):
		result = "<?xml version=\"1.0\"?>"
		result += "<?xml-stylesheet type=\"text/xsl\" href=\"/static/style.xsl\"?>\n"
		result += '<page>' + xml + '</page>'
		self.response.headers['Content-Type'] = 'application/xml; charset=utf-8'
		self.response.out.write(result)

	def quote(self, text):
		return urllib.quote(text.encode('utf8'))

	def unquote(self, text):
		return urllib.unquote(text).decode('utf8')

def run(rules):
	_DEBUG = ('Development/' in os.environ.get('SERVER_SOFTWARE'))
	_DEBUG = True
	if _DEBUG:
		logging.getLogger().setLevel(logging.DEBUG)
	application = webapp.WSGIApplication(rules, debug=_DEBUG)
	wsgiref.handlers.CGIHandler().run(application)
