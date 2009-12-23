# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Всё, что нужно для работы с Amazon S3.
#
# Настройки обслуживает класс S3Settings, его следует
# прикрепить к нужному пути (напр., /upload/settings).

import base64, datetime, hmac, hashlib, logging, random

from google.appengine.ext import db
from google.appengine.api import users

from base import BaseRequestHandler

def encode_policy(dict):
	return base64.b64encode(unicode(dict).encode('utf-8'))

def sign(settings, string):
	dm = hmac.new(settings.s3s, string, hashlib.sha1)
	return base64.b64encode(dm.digest())

def create_id():
	"""
	Возвращает случайный идентификатор для загрузки файла.
	"""
	# FIXME: придумать что-нибудь по-лучше
	return hmac.new('key', str(random.random()), hashlib.md5).hexdigest()

class S3Settings(db.Model):
	"""
	Класс для хранения настроек S3 в базе данных.
	"""
	s3a = db.StringProperty()
	s3s = db.StringProperty()
	bucket = db.StringProperty()

	@classmethod
	def load(cls):
		"""
		Loads settings from the database, creates if necessary.
		"""
		s = cls.all().get()
		if s is None:
			s = cls()
		return s

class S3File(db.Model):
	"""
	Класс для хранения загруженных файлов.
	"""
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)
	bucket = db.StringProperty()
	path = db.StringProperty()
	size = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	info = db.TextProperty()
	owner = db.UserProperty()

class S3SettingsHandler(BaseRequestHandler):
	"""
	Обработчик формы редактирования настроек S3.
	Доступен только администраторам.
	"""
	def get(self):
		self.force_admin()
		s = S3Settings.load()
		return self.sendXML(self.formatXML('s3-settings',
			action=self.request.path,
			s3a=s.s3a,
			s3s=s.s3s,
			bucket=s.bucket))

	def post(self):
		self.force_admin()
		s = S3Settings.load()
		for k in ('s3a', 's3s', 'bucket'):
			setattr(s, k, self.request.get(k))
		s.put()
		self.redirect(self.request.path)

class S3UploadHandler(BaseRequestHandler):
	def get(self):
		if self.request.get('key'):
			return self.get_confirm()

		base = self.getBaseURL()
		settings = S3Settings.load()

		path = create_id()
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

		logging.debug(policy_src)

		return self.sendXML(self.mkem('s3-upload-form', {
			'bucket': settings.bucket,
			'access-key': settings.s3a,
			'key': path + '/${filename}',
			'policy': policy,
			'signature': sign(settings, policy),
			'base': base,
			'owner': users.get_current_user().nickname(),
		}))

	def get_confirm(self):
		last = S3File.gql('ORDER BY id DESC').get()
		if last is None:
			id = 1
		else:
			id = last.id + 1

		File = S3File(id=id,
			name=self.request.get('key').split('/')[-1],
			bucket=self.request.get('bucket'),
			path=self.request.get('key'),
			owner=users.get_current_user())
		File.put()

		self.redirect('/?file=' + str(File.id))
