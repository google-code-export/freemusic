# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging
import urllib
from xml.sax.saxutils import escape
from google.appengine.ext import db

class SiteUser(db.Model):
	user = db.UserProperty()
	joined = db.DateTimeProperty(auto_now_add=True)
	weight = db.FloatProperty()

class SiteArtist(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)

class SiteAlbum(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist)
	release_date = db.DateProperty(auto_now_add=True)
	rating = db.RatingProperty() # average album rate
	cover_small = db.LinkProperty() # image URL
	cover_large = db.LinkProperty() # image URL
	xml = db.TextProperty() # updated on save

	def put(self, quick=False):
		if not quick:
			self.xml = self.to_xml()
		db.Model.put(self)

	def to_xml(self):
		xml = u'<album id="%u" name="%s" artist="%s" pubDate="%s">' % (self.id, escape(self.name), escape(self.artist.name), self.release_date.isoformat())
		xml += self.get_children_xml(SiteTrack, u'tracks')
		xml += self.get_children_xml(SiteImage, u'images')
		xml += self.get_children_xml(SiteFile, u'files')
		xml += u'</album>'
		return xml

	def get_children_xml(self, cls, em):
		xml = u''
		children = cls.gql('WHERE album = :1', self).fetch(1000)
		if children:
			xml += u'<' + em + u'>'
			for child in children:
				xml += child.to_xml()
			xml += u'</' + em + u'>'
		return xml

class SiteImage(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	uri = db.LinkProperty()
	width = db.IntegerProperty()
	height = db.IntegerProperty()
	type = db.StringProperty()

	def to_xml(self):
		return u"<image uri='%s' width='%u' height='%u' type='%s'/>" % (escape(self.uri), self.width, self.height, escape(self.type))

class SiteTrack(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	title = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist) # for compilations
	lyrics = db.TextProperty()
	number = db.IntegerProperty()
	mp3_link = db.LinkProperty()

	def to_xml(self):
		xml = u'<track number="%u" title="%s" mp3="%s"/>' % (self.number, escape(self.title), escape(self.mp3_link))
		return xml

class SiteFile(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	name = db.StringProperty()
	uri = db.LinkProperty()
	type = db.StringProperty()
	size = db.IntegerProperty()

	def to_xml(self):
		xml = u"<file name='%s' uri='%s' type='%s'" % (escape(self.name), escape(self.uri), escape(self.type))
		if self.size:
			xml += u" size='%u'" % self.size
		return xml + u'/>'

class SiteAlbumReview(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	author = db.ReferenceProperty(SiteUser)
	created = db.DateTimeProperty(auto_now_add=True)
