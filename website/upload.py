# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import base64, hmac, hashlib

# Python imports
import datetime, time
import logging
import urllib
from xml.dom.minidom import parseString

# GAE imports
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import login_required

# Site imports
from base import BaseRequestHandler, run, HTTPException
from s3 import S3File
import model, myxml, mail

class Remote(BaseRequestHandler):
	def get(self):
		self.force_user()
		self.sendXML(u'<upload-remote/>')

	def post(self):
		user = self.force_user()
		url = self.request.get('url')
		if not url:
			raise HTTPException(400, u'Не указан адрес ZIP-архива.')
		file = S3File.gql('WHERE uri = :1', url).get()
		if file:
			raise HTTPException(400, u'Этот файл уже был загружен.')
		file = S3File(uri=url, name=url.split('/')[-1], owner=user)
		file.put()
		self.sendXML(myxml.em(u's3-upload-ok', {
			'file-id': file.id,
		}))

def sign(password, string):
	dm = hmac.new(password, string, hashlib.sha1)
	return base64.b64encode(dm.digest())
