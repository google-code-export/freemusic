# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# GAE imports
from google.appengine.api import users
from google.appengine.ext import db

# Local imports
import myxml
from base import BaseRequestHandler, NotFoundException
from s3 import S3File, sign

class APIRequest(BaseRequestHandler):
	def check_access(self, text):
		if self.request.get('signature') != sign(text):
			self.force_admin()

class Queue(BaseRequestHandler):
	def get(self):
		if self.request.path == '/api/queue.yaml':
			return self.get_yaml()
		xml = u''
		for file in S3File.all().fetch(1000):
			if not file.uri:
				file.uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			xml += myxml.em(u'file', {
				'id': file.id,
				'name': file.name,
				'owner': file.owner,
				'uri': file.uri,
			})
		self.sendXML(myxml.em(u'queue', content=xml))

	def get_yaml(self):
		yaml = u''
		for file in S3File.all().fetch(1000):
			uri = file.uri
			if not uri and file.bucket and file.path:
				uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			yaml += u'- id: %u\n' % file.id
			yaml += u'  uri: %s\n' % uri
			if file.owner:
				yaml += u'  owner: %s\n' % file.owner
		self.sendText(yaml)


class Delete(APIRequest):
	def get(self):
		id = self.request.get('id')
		if not id:
			raise Exception('Queue id not specified.')
		self.check_access(id)
		file = S3File.gql('WHERE id = :1', int(id)).get()
		if not file:
			raise NotFoundException()
		file.delete()
		self.redirect('/api/queue.xml')
