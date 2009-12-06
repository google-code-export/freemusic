# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import urllib
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

class SiteImage(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	uri = db.LinkProperty()
	width = db.IntegerProperty()
	height = db.IntegerProperty()
	cover = db.BooleanProperty()

class SiteTrack(db.Model):
	title = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist) # for compilations
	lyrics = db.TextProperty()
	number = db.IntegerProperty()
	mp3_link = db.LinkProperty()

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
