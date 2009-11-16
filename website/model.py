# -*- coding: utf-8 -*-
# vim: set ts=2 sts=2 sw=2 et:

from google.appengine.ext import db

class SiteUser(db.Model):
  user = db.UserProperty()
  joined = db.DateTimeProperty(auto_now_add=True)
  weight = db.FloatProperty()

class SiteArtist(db.Model):
  name = db.StringProperty(required=True)

class SiteTrack(db.Model):
  name = db.StringProperty()
  number = db.IntegerProperty()
  mp3_link = db.LinkProperty()

class SiteAlbum(db.Model):
  name = db.StringProperty()
  artist = db.ReferenceProperty(SiteArtist)
  release_date = db.DateTimeProperty(auto_now_add=True)
  rating = db.RatingProperty() # average album rate
  cover_small = db.LinkProperty() # image URL
  cover_large = db.LinkProperty() # image URL
  tracks = db.BlobProperty()
  files = db.BlobProperty()

class SiteAlbumReview(db.Model):
  album = db.ReferenceProperty(SiteAlbum)
  author = db.ReferenceProperty(SiteUser)
  created = db.DateTimeProperty(auto_now_add=True)
