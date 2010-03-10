# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

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
from s3 import S3File, sign
import mail
import model
import myxml
import settings
import util

class Remote(BaseRequestHandler):
	xsltName = 'upload.xsl'
	tabName = 'personal'

	def get(self):
		self.force_user()
		self.sendXML(myxml.em(u'upload-remote', {
			'robot-is-online': util.robot.is_online(),
		}))

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

class Queue(BaseRequestHandler):
	xsltName = 'upload.xsl'

	def get(self):
		s = settings.get()
		xml = u''.join([f.to_xml() for f in S3File.all().fetch(1000)])
		self.sendXML(myxml.em(u'queue', {
			'moderator': s.album_moderator,
		}, content=xml))

	def post(self):
		id = int(self.request.get('id'))
		url = str(self.request.get('url'))
		if self.request.get('signature') != sign(url):
			raise Exception('Bad Signature')
		file = S3File.gql('WHERE id = :1', id).get()
		if file is None:
			raise Exception('Queue item not found.')
		file.xml = url
		file.put()

if __name__ == '__main__':
	run([
		('/upload/queue', Queue),
		('/upload/remote', Remote),
	])
