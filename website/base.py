# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, os, urllib

# GAE imports
import wsgiref.handlers
from google.appengine.ext import webapp

class BaseRequestHandler(webapp.RequestHandler):
	def render(self, template_name, vars={}, content_type='text/xml'):
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		result = template.render(path, vars)
		self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
		self.response.out.write(result)

	def quote(self, text):
		return urllib.quote(text.encode('utf8'))

	def unquote(self, text):
		return urllib.unquote(text).decode('utf8')
