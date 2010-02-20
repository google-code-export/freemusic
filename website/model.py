# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging
import urllib
from xml.sax.saxutils import escape
from google.appengine.api import users
from google.appengine.ext import db

import myxml as xml

def get_current_user():
	user = SiteUser.gql('WHERE user = :1', users.get_current_user()).get()
	return user

class SiteUser(db.Model):
	user = db.UserProperty(required=True)
	joined = db.DateTimeProperty(auto_now_add=True)
	weight = db.FloatProperty()
	invited = db.BooleanProperty(required=True)

	def to_xml(self):
		return xml.em(u'user', {
			'nickname': self.user.nickname(),
			'email': self.user.email(),
			'weight': self.weight,
			'invited': self.invited,
		})

class SiteArtist(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)
	xml = db.TextProperty()

	def put(self, quick=False):
		if not self.id:
			self.id = nextId(SiteArtist)
			logging.info('New artist: %s (artist/%u)' % (self.name, self.id))
		if not quick:
			self.xml = self.to_xml()
		return db.Model.put(self)

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
	cover_small = db.LinkProperty() # image URL; FIXME: не используется
	cover_large = db.LinkProperty() # image URL
	labels = db.StringListProperty()
	owner = db.UserProperty()
	xml = db.TextProperty() # updated on save
	album_xml = db.LinkProperty() # ссылка на исходный album.xml, для отлова дублей
	rate = db.RatingProperty() # средняя оценка альбома, обновляется в album.Review.post()

	def put(self, quick=False):
		if not self.id:
			self.id = nextId(SiteAlbum)
			logging.info('New album: %s (album/%u)' % (self.name, self.id))
		if not quick:
			self.rate = self.get_avg_rate()
			self.xml = self.to_xml()
			logging.info('album/%u: xml updated' % self.id)
		return db.Model.put(self)

	def get_avg_rate(self):
		rates = [r.rate_average for r in SiteAlbumReview.gql('WHERE album = :1', self).fetch(1000) if r.rate_average is not None]
		if len(rates):
			return sum(rates) / len(rates)

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
			'text': self.text,
			'rate': self.rate,
		}, content)

	def get_children_xml(self, cls, em):
		return xml.em(em, content=u''.join([c.to_xml() for c in cls.gql('WHERE album = :1', self).fetch(1000)]))

	def tracks(self):
		tr = SiteTrack.gql('WHERE album = :1', self).fetch(1000)
		if not tr:
			tr = []
		return tr

class SiteImage(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	medium = db.LinkProperty()
	original = db.LinkProperty()
	type = db.StringProperty()

	def to_xml(self):
		return xml.em(u'image', {
			'medium': self.medium,
			'original': self.original,
			'type': self.type,
		})

class SiteTrack(db.Model):
	id = db.IntegerProperty()
	album = db.ReferenceProperty(SiteAlbum)
	title = db.StringProperty()
	artist = db.ReferenceProperty(SiteArtist) # for compilations
	lyrics = db.TextProperty()
	number = db.IntegerProperty()
	mp3_link = db.LinkProperty()
	mp3_length = db.IntegerProperty() # нужно для RSS с подкастом
	ogg_link = db.LinkProperty()
	ogg_length = db.IntegerProperty() # нужно для RSS с подкастом
	duration = db.StringProperty()

	def put(self):
		if not self.id:
			self.id = nextId(SiteTrack)
		return db.Model.put(self)

	def to_xml(self):
		return xml.em(u'track', {
			'id': self.id,
			'number': self.number,
			'album-id': self.album.id,
			'album-name': self.album.name,
			'title': self.title,
			'duration': self.duration,
			'mp3-link': self.mp3_link,
			'ogg-link': self.ogg_link,
			'lyrics': self.lyrics,
		})

class SiteFile(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	name = db.StringProperty()
	uri = db.LinkProperty()
	type = db.StringProperty()
	size = db.IntegerProperty()

	def to_xml(self):
		return xml.em(u'file', {
			'name': self.name,
			'uri': self.uri,
			'type': self.type,
		})

class SiteAlbumReview(db.Model):
	# рецензируемый альбом
	album = db.ReferenceProperty(SiteAlbum)
	# автор рецензии
	author = db.ReferenceProperty(SiteUser)
	# дата написания рецензии
	published = db.DateTimeProperty(auto_now_add=True)
	# оценки
	rate_sound = db.RatingProperty()
	rate_arrangement = db.RatingProperty()
	rate_vocals = db.RatingProperty()
	rate_lyrics = db.RatingProperty()
	rate_prof = db.RatingProperty()
	rate_average = db.RatingProperty()
	# комментарий
	comment = db.TextProperty()
	# кэш
	xml = db.TextProperty()

	def put(self):
		if self.author is None:
			self.author = get_current_user()
		self.rate_average = self.get_avg()
		self.xml = self.to_xml()
		return db.Model.put(self)

	def to_xml(self):
		return xml.em(u'review', {
			'pubDate': self.published.isoformat(),
			'album-id': self.album.id,
			'album-name': self.album.name,
			'author-nickname': self.author.user.nickname(),
			'author-email': self.author.user.email(),
			'sound': self.rate_sound,
			'arrangement': self.rate_arrangement,
			'vocals': self.rate_vocals,
			'lyrics': self.rate_lyrics,
			'prof': self.rate_prof,
			'average': self.rate_average,
			'comment': self.comment,
		})

	def get_avg(self):
		rates = [rate for rate in [self.rate_sound, self.rate_arrangement, self.rate_vocals, self.rate_lyrics, self.rate_prof] if rate is not None]
		if len(rates):
			return sum(rates) / len(rates)
		return None

def nextId(cls):
	last = cls.gql('ORDER BY id DESC').get()
	if last:
		return last.id + 1
	return 1
