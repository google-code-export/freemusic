# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# GAE imports
from google.appengine.api import users
from google.appengine.ext import db

# Local imports
import myxml
from base import BaseRequestHandler, NotFoundException
from s3 import S3File

def check_signature(text):
	return True

class Queue(BaseRequestHandler):
	def get(self):
		if self.request.path == '/api/queue.yaml':
			return self.get_yaml()
		xml = u''
		for file in S3File.all().fetch(1000):
			uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			xml += myxml.em(u'file', {
				'id': file.id,
				'name': file.name,
				'owner': file.owner,
				'uri': 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path,
			})
		self.sendXML(myxml.em(u'queue', content=xml))

	def get_yaml(self):
		yaml = u'files:\n'
		for file in S3File.all().fetch(1000):
			uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			yaml += u'  - id: %u\n' % file.id
			yaml += u'    name: %s\n' % file.name
			if file.owner:
				yaml += u'    owner: %s\n' % file.owner
			yaml += u'    uri: %s\n' % uri
		self.sendText(yaml)


class Delete(BaseRequestHandler):
	def get(self):
		id = self.request.get('id')
		if not id:
			raise Exception('Queue id not specified.')
		check_signature(id)
		file = S3File.gql('WHERE id = :1', int(id)).get()
		if not file:
			raise NotFoundException()
		file.delete()
		self.redirect('/api/queue.xml')
