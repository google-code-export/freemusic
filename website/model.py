# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import hashlib
import logging
import urllib

from xml.sax.saxutils import escape
from google.appengine.api import users
from google.appengine.ext import db

import myxml as xml
import util

def get_current_user():
	user = SiteUser.gql('WHERE user = :1', users.get_current_user()).get()
	return user

def nextId(cls):
	last = cls.gql('ORDER BY id DESC').get()
	if last:
		return last.id + 1
	return 1

class SiteUser(db.Model):
	user = db.UserProperty(required=True)
	joined = db.DateTimeProperty(auto_now_add=True)
	weight = db.FloatProperty()
	invited = db.BooleanProperty(required=True)
	nickname = db.StringProperty()

	def to_json(self):
		return {
			'email': self.user.email(),
			'joined': self.joined.strftime('%Y-%m-%d %H:%M:%S'),
			'weight': self.weight,
			'nickname': self.nickname,
		}

class SiteArtist(db.Model):
	id = db.IntegerProperty()
	name = db.StringProperty(required=True)
	sortname = db.StringProperty(required=False)

	def to_json(self):
		return {
			'id': self.id,
			'name': self.name,
		}

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
	album_xml = db.LinkProperty() # ссылка на исходный album.xml, для отлова дублей
	rate = db.RatingProperty() # средняя оценка альбома, обновляется в album.Review.post()

	def to_json(self):
		return {
			'id': self.id,
			'name': self.name,
			'text': self.text,
			'artist': self.artist.id,
			'release_date': self.release_date.strftime('%Y-%m-%d %H:%M:%S'),
			'rating': self.rating or self.rate,
			'cover_small': self.cover_small,
			'cover_large': self.cover_large,
			'labels': self.labels,
			'owner': self.owner.email(),
			'album_xml': self.album_xml,
		}

	def put(self, quick=False):
		if not self.id:
			self.id = nextId(SiteAlbum)
			logging.info('New album: %s (album/%u)' % (self.name, self.id))
		if not quick:
			self.rate = self.get_avg_rate()
			self.xml = self.to_xml()
			self.update_shortxml()
			logging.info('album/%u: xml updated' % self.id)
		return db.Model.put(self)

	def get_avg_rate(self):
		rates = [r.rate_average for r in SiteAlbumReview.gql('WHERE album = :1', self).fetch(1000) if r.rate_average is not None]
		if len(rates):
			return sum(rates) / len(rates)

	def update_shortxml(self):
		image = None
		for img in SiteImage.gql('WHERE album = :1', self).fetch(10):
			if img.type == 'front':
				image = img.medium
				break
		self.shortxml = xml.em(u'album', {
			'id': self.id,
			'name': self.name,
			'artist-id': self.artist.id,
			'artist-name': self.artist.name,
			'pubDate': self.release_date.isoformat(),
			'rate': self.rate,
			'image': image,
		})

class SiteAlbumStar(db.Model):
	"Хранит информацию о любимых альбомах пользователей."
	album = db.ReferenceProperty(SiteAlbum)
	user = db.UserProperty()
	added = db.DateTimeProperty(auto_now_add=True)

	def to_json(self):
		return {
			# 'album': self.album and self.album.id,
			'user': self.user.email(),
			'added': self.added.strftime('%Y-%m-%d %H:%M:%S'),
		}

class SiteImage(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	medium = db.LinkProperty()
	original = db.LinkProperty()
	type = db.StringProperty()

	def to_json(self):
		return {
			'album': self.album.id,
			'medium': self.medium,
			'original': self.original,
			'type': self.type,
		}

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

	def to_json(self):
		return {
			'id': self.id,
			'album': self.album and self.album.id,
			'title': self.title,
			'artist': self.artist and self.artist.id,
			'lyrics': self.lyrics,
			'number': self.number,
			'mp3_link': self.mp3_link,
			'mp3_length': self.mp3_length,
			'ogg_link': self.ogg_link,
			'ogg_length': self.ogg_length,
			'duration': self.duration,
		}

class SiteFile(db.Model):
	album = db.ReferenceProperty(SiteAlbum)
	name = db.StringProperty()
	uri = db.LinkProperty()
	type = db.StringProperty()
	size = db.IntegerProperty()

	def to_json(self):
		return {
			'album': self.album.id,
			'name': self.name,
			'uri': self.uri,
			'type': self.type,
			'size': self.size,
		}

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

	def to_json(self):
		return {
			'album': self.album.id,
			'author': self.author.user.email(),
			'published': self.published.strftime('%Y-%m-%d %H:%M:%S'),
			'rate_sound': self.rate_sound,
			'rate_arrangement': self.rate_arrangement,
			'rate_vocals': self.rate_vocals,
			'rate_lyrics': self.rate_lyrics,
			'rate_prof': self.rate_prof,
			'rate_average': self.rate_average,
			'comment': self.comment,
		}

	def put(self):
		if self.author is None:
			self.author = get_current_user()
		self.rate_average = self.get_avg()
		return db.Model.put(self)

	def get_avg(self):
		rates = [rate for rate in [self.rate_sound, self.rate_arrangement, self.rate_vocals, self.rate_lyrics, self.rate_prof] if rate is not None]
		if len(rates):
			return sum(rates) / len(rates)
		return None

	def to_rss(self):
		description = u''
		if self.comment:
			description += u'<p>' + self.comment + u'</p>'
		if self.rate_average:
			description += u'<p>Общая оценка: ' + unicode(self.rate_average) + u'/5.</p>'
		return {
			'title': u'Рецензия на «%s» от %s' % (self.album.name, self.album.artist.name),
			'link': 'album/' + str(self.album.id) + '#review:' + self.author.user.nickname(),
			'description': description,
			'author': self.author.user.email(),
		}

class SiteEvent(db.Model):
	artist = db.ReferenceProperty(SiteArtist)
	id = db.IntegerProperty()

	def to_json(self):
		return {
			'id': self.id,
			'artist': self.artist.id,
		}

class SiteAlbumLabel(db.Model):
	"""
	Метка для альбома. Используется для хранения сырых данных,
	которые в сыром виде не используются: они периодически
	агрегируются, результаты сохраняются в SiteAlbum.

	Метки есть только у альбомов. Метки исполнителя формируются
	на основании меток его альбомов.
	"""
	# Метка.
	label = db.StringProperty()
	# Пользователь, добавивший метку.
	user = db.UserProperty(required=True)
	# Альбом, к которому относится метка.
	album = db.ReferenceProperty(SiteAlbum)
	# Дата установки, на всякий случай.
	published = db.DateTimeProperty(auto_now_add=True)

	def to_json(self):
		return {
			'label': self.label,
			'user': self.user.email(),
			'album': self.album.id,
			'published': self.published.strftime('%Y-%m-%d %H:%M:%S'),
		}
