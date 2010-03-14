# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Классы для работы с Amazon S3.  Из того, что можно использовать во вне:
#
# S3File:
#   Используется для хранения информации о загруженных файлах.
#
# S3SettingsHandler:
#   Настройка доступа, можно прикрепить к нужному пути,
#   например: /upload/settings.
#
# S3UploadHandler:
#   Вывод и обработка формы загрузки файла в хранилище.  Можно прикрепить
#   к нужному пути, например: /upload.

import base64, datetime, hmac, hashlib, logging, random

from google.appengine.ext import db
from google.appengine.api import users

from base import BaseRequestHandler, HTTPException
import myxml as xml
import util

class S3File(db.Model):
	"""
	Класс для хранения загруженных файлов.
	"""
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)
	bucket = db.StringProperty()
	path = db.StringProperty()
	uri = db.LinkProperty()
	size = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	info = db.TextProperty()
	owner = db.UserProperty()
	xml = db.LinkProperty()

	def put(self):
		if not self.id:
			self.id = S3File.getNextId()
		return db.Model.put(self)

	def to_xml(self):
		return xml.em(u'S3File', {
			'id': self.id,
			'name': self.name,
			'file-uri': self.uri,
			'created': self.created,
			'owner': self.owner,
			'xml-uri': self.xml,
			'size': self.size,
		})

	@classmethod
	def getNextId(cls):
		last = cls.gql('ORDER BY id DESC').get()
		if last:
			return last.id + 1
		return 1

class S3Settings(db.Model):
	"""
	Класс для хранения настроек S3 в базе данных.
	"""
	s3a = db.StringProperty()
	s3s = db.StringProperty()
	bucket = db.StringProperty()
	after = db.StringProperty()

	@classmethod
	def load(cls):
		"""
		Loads settings from the database, creates if necessary.
		"""
		s = cls.all().get()
		if s is None:
			s = cls()
		return s

class S3SettingsHandler(BaseRequestHandler):
	xsltName = 'upload.xsl'

	"""
	Обработчик формы редактирования настроек S3.  Доступен только
	администраторам.  Выдаёт наружу элемент <s3-settings>.
	"""
	def get(self):
		self.force_admin()
		s = S3Settings.load()
		return self.sendXML(xml.em(u's3-settings', {
			'action': self.request.path,
			's3a': s.s3a,
			's3s': s.s3s,
			'bucket': s.bucket,
			'after': s.after
			}))

	def post(self):
		self.force_admin()
		s = S3Settings.load()
		for k in ('s3a', 's3s', 'bucket'):
			setattr(s, k, self.request.get(k))
		s.put()
		self.redirect('/settings')

class S3UploadHandler(BaseRequestHandler):
	xsltName = 'upload.xsl'
	tabName = 'personal'

	"""
	Обслуживание формы загрузки файла в хранилище Amazon S3.
	"""
	def get(self):
		user = self.force_user()

		if self.request.get('key'):
			return self.get_confirm()

		if 'ok' in self.request.arguments():
			return self.get_ok()

		base = self.getBaseURL()
		settings = S3Settings.load()

		path = user.email() + '/' + str(S3File.getNextId())

		policy_src = {
			'expiration': (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat() + 'Z',
			'conditions': [
				{ 'acl': 'public-read' },
				{ 'bucket': str(settings.bucket) },
				[ 'starts-with', '$key', path + '/' ],
				[ 'starts-with', '$success_action_redirect', base ],
			],
		}
		policy = encode_policy(policy_src)

		# logging.debug(policy_src)

		return self.sendXML(xml.em('s3-upload-form', {
			'bucket': settings.bucket,
			'access-key': settings.s3a,
			'key': path + '/${filename}',
			'policy': policy,
			'signature': sign(policy, settings),
			'base': base,
			'owner': users.get_current_user().email(),
			'robot-is-online': util.robot.is_online(),
		}))

	def get_confirm(self):
		id = S3File.getNextId()

		File = S3File(id=id,
			name=self.request.get('key').split('/')[-1],
			bucket=self.request.get('bucket'),
			path=self.request.get('key'),
			uri='http://' + self.request.get('bucket') + '.s3.amazonaws.com/' + self.request.get('key'),
			owner=users.get_current_user())
		r = util.head(File.uri)
		if r.status_code == 200 and 'Content-Length' in r.headers:
			File.size = int(r.headers['Content-Length'])
		File.put()

		self.redirect(self.request.path + '?ok=' + str(File.id))

	def get_ok(self):
		self.sendXML('<s3-upload-ok file-id="%u"/>' % int(self.request.get('ok')))

	def handle_exception(self, e, debug_mode):
		"""
		Заменяет ошибку 401 на сообщение с просьбой войти.
		"""
		if type(e) == HTTPException and e.code == 401:
			self.sendXML('<s3-login-message/>')
		else:
			BaseRequestHandler.handle_exception(self, e, debug_mode)

def encode_policy(dict):
	return base64.b64encode(unicode(dict).encode('utf-8'))

def sign(string, settings=None):
	if settings is None:
		settings = S3Settings.load()
	if not settings.is_saved():
		raise HTTPException(503, u'Отсутствуют <a href="/upload/settings">настройки S3</a>, загрузка файлов невозможна.')
	dm = hmac.new(settings.s3s, string, hashlib.sha1)
	return base64.b64encode(dm.digest())
