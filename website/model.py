# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging
import urllib
from xml.sax.saxutils import escape
from google.appengine.ext import db

import myxml as xml

class SiteUser(db.Model):
	user = db.UserProperty()
	joined = db.DateTimeProperty(auto_now_add=True)
	weight = db.FloatProperty()

class SiteArtist(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)
	xml = db.TextProperty()

	def put(self, quick=False):
		if not quick:
			self.xml = self.to_xml()
		db.Model.put(self)

	def to_xml(self):
		albums = xml.em(u'albums', content=u''.join([album.xml for album in SiteAlbum.gql('WHERE artist = :1', self).fetch(100)]), empty=False)
		return xml.em(u'artist', attrs={
			'id': self.id,
			'name': self.name,
		}, content=albums)

class SiteAlbum(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty()
	text = db.TextProperty()
	artist = db.ReferenceProperty(SiteArtist)
	release_date = db.DateProperty(auto_now_add=True)
	rating = db.RatingProperty() # average album rate
	cover_small = db.LinkProperty() # image URL
	cover_large = db.LinkProperty() # image URL
	labels = db.StringListProperty()
	owner = db.UserProperty()
	xml = db.TextProperty() # updated on save

	def put(self, quick=False):
		if not quick:
			self.xml = self.to_xml()
			logging.info('album/%u: xml updated' % self.id)
		db.Model.put(self)

	def to_xml(self):
		content = self.get_children_xml(SiteTrack, u'tracks') + self.get_children_xml(SiteImage, u'images') + self.get_children_xml(SiteFile, u'files')
		if self.labels:
			content += xml.em(u'labels', content=u''.join([xml.em(u'label', {'uri':xml.uri(label)}, content=label) for label in self.labels]))
		return xml.em(u'album', {
			'id': self.id,
			'name': self.name,
			'artist-id': self.artist.id,
			'artist-name': self.artist.name,
			'pubDate': self.release_date.isoformat(),
			'owner': self.owner,
			'text': self.text
		}, content)

	def get_children_xml(self, cls, em):
		return xml.em(em, content=u''.join([c.to_xml() for c in cls.gql('WHERE album = :1', self).fetch(1000)]))

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
