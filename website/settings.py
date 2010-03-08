# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Вывод главной страницы настроек.
"""

from google.appengine.ext import db

import base
import myxml

class Settings(db.Model):
	album_moderator = db.StringProperty()

class SettingsPage(base.BaseRequestHandler):
	xsltName = 'settings.xsl'

	def get(self):
		self.force_admin()
		settings = get()
		self.sendXML(myxml.em(u'settings', {
			'album_moderator': settings.album_moderator,
		}))

	def post(self):
		self.force_admin()
		settings = get()
		settings.album_moderator = self.request.get('album_moderator')
		settings.put()
		self.redirect(self.request.path)

def get():
	return Settings.all().get() or Settings()
