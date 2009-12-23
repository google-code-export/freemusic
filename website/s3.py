# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Всё, что нужно для работы с Amazon S3.
#
# Настройки обслуживает класс S3Settings, его следует
# прикрепить к нужному пути (напр., /upload/settings).

from google.appengine.ext import db
from base import BaseRequestHandler

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
