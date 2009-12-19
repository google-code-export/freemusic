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
	name = db.StringProperty(required=True)

class SiteAlbum(db.Model):
	name = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist)
	release_date = db.DateProperty(auto_now_add=True)
	rating = db.RatingProperty() # average album rate
	cover_small = db.LinkProperty() # image URL
	cover_large = db.LinkProperty() # image URL
	xml = db.TextProperty() # updated on save

	def put(self, quick=False):
		if not quick:
			self.xml = self.get_xml()
		db.Model.put(self)

	def get_xml(self):
		xml = u'<album name="%s" artist="%s">' % (escape(self.name), escape(self.artist.name))
		xml += self.get_tracks_xml()
		xml += u'</album>'
		return xml

	def get_tracks_xml(self):
		xml = u''
		tracks = SiteTrack.gql('WHERE album = :1', self).fetch(1000)
		if tracks:
			xml += u'<tracks>'
			for track in tracks:
				xml += track.xml()
			xml += u'</tracks>'
		return xml

class SiteImage(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	uri = db.LinkProperty()
	width = db.IntegerProperty()
	height = db.IntegerProperty()
	cover = db.BooleanProperty()

class SiteTrack(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	title = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist) # for compilations
	lyrics = db.TextProperty()
	number = db.IntegerProperty()
	mp3_link = db.LinkProperty()

	def xml(self):
		xml = u'<track number="%u" title="%s" mp3="%s"/>' % (self.number, escape(self.title), escape(self.mp3_link))
		return xml

class SiteFile(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	name = db.StringProperty()
	uri = db.LinkProperty()
	type = db.StringProperty()
	size = db.IntegerProperty()

class SiteAlbumReview(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	author = db.ReferenceProperty(SiteUser)
	created = db.DateTimeProperty(auto_now_add=True)
