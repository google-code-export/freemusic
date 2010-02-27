# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Вывод случайных текстовых фраз на главной странице. Фразы могут
содержать ссылки, можно листать вперёд-назад (на самом деле они
выводятся в случайном порядке). В будущем будет лучше заменить
это на RSS ленту.
"""

import random

from google.appengine.ext import db

import base
import myxml

class SiteClip(db.Model):
	text = db.TextProperty(required=True)
	url = db.LinkProperty()
	added = db.DateTimeProperty(auto_now_add=True)

class ShowClips(base.BaseRequestHandler):
	xsltName = 'clips.xsl'

	def get(self):
		self.force_admin()
		xml = u''
		for clip in SiteClip.all().fetch(1000):
			xml += myxml.em(u'clip', {'url': clip.url}, content=myxml.cdata(clip.text))
		self.sendXML(myxml.em(u'clips', content=xml))

	def post(self):
		clip = SiteClip(text=self.request.get('text'), url=self.request.get('url'))
		clip.put()
		self.redirect('/clips')

class GetRandomClip(base.BaseRequestHandler):
	def get(self):
		clips = SiteClip.all().order('-added').fetch(10)
		clip = clips.pop(random.randint(0, len(clips)-1))
		text = clip.text
		if clip.url:
			text += u' ' + myxml.em(u'a', {'href': clip.url, 'class': 'ext'}, content=u'Подробнее…')
		self.sendJSON({ 'text': text })

class GetRecentClips(base.BaseRequestHandler):
	def get(self):
		xml = u''
		for clip in SiteClip.all().order('-added').fetch(10):
			text = clip.text
			if clip.url:
				text += u' ' + myxml.em(u'a', {'href': clip.url, 'class': 'ext'}, content=u'Подробнее…')
			xml += myxml.em(u'li', content=text)
		self.sendXML(myxml.em(u'ul', content=xml))
