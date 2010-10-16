# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import hashlib
import logging
import urllib

from xml.sax.saxutils import escape
from google.appengine.api import users
from google.appengine.ext import db

import util

_REQUIRED = False # normally True, False for import only (FIXME)

def get_current_user():
    user = SiteUser.gql('WHERE user = :1', users.get_current_user()).get()
    return user

def nextId(cls):
    last = cls.gql('ORDER BY id DESC').get()
    if last:
        return last.id + 1
    return 1

class CustomModel(db.Model):
    JSON_TYPE_MAP = {
        'SiteAlbum': lambda x: x.id,
        'SiteArtist': lambda x: x.id,
        'datetime': lambda x: x.strftime('%Y-%m-%d %H:%M:%S'),
        'date': lambda x: x.strftime('%Y-%m-%d'),
        'User': lambda x: x.email(),
        'SiteUser': lambda x: x.user.email(),
    }

    def to_json(self):
        result = {}
        for k in self.fields():
            try:
                val = getattr(self, k)
            except Exception, e:
                logging.error(e)
                val = None # ReferenceProperty скорее всего
            if self.JSON_TYPE_MAP.has_key(val.__class__.__name__):
                val = self.JSON_TYPE_MAP[val.__class__.__name__](val)
            elif isinstance(val, CustomModel):
                raise Exception(val)
            result[k] = val
        return result

    def from_json(self, json):
        converters = {
            'IntegerProperty': int,
        }

        for k in json:
            if k in self.fields():
                if not json[k]:
                    setattr(self, k, None)
                else:
                    cls = self.fields()[k].__class__.__name__
                    val = cls in converters and converters[cls](json[k]) or json[k]
                    setattr(self, k, val)
        return self

class SiteUser(CustomModel):
    user = db.UserProperty(required=_REQUIRED)
    joined = db.DateTimeProperty(auto_now_add=True)
    weight = db.FloatProperty()
    nickname = db.StringProperty()

class SiteArtist(CustomModel):
    id = db.IntegerProperty()
    name = db.StringProperty(required=_REQUIRED)
    sortname = db.StringProperty(required=False)
    twitter = db.StringProperty()
    lastfm_name = db.StringProperty()

class SiteAlbum(CustomModel):
    id = db.IntegerProperty()
    name = db.StringProperty()
    text = db.TextProperty()
    artists = db.StringListProperty() # all involved artists, updated automatically from tracks
    release_date = db.DateProperty(auto_now_add=True)
    homepage = db.LinkProperty()
    rating = db.RatingProperty() # average album rate
    cover_id = db.StringProperty() # blobstore key
    cover_large = db.LinkProperty()
    cover_small = db.LinkProperty()
    labels = db.StringListProperty()
    owner = db.UserProperty()
    rate = db.RatingProperty() # средняя оценка альбома, обновляется в album.Review.post()

    def put(self, quick=False):
        if not self.id:
            self.id = nextId(SiteAlbum)
            logging.info('New album: %s (album/%u)' % (self.name, self.id))
        return CustomModel.put(self)

    def get_avg_rate(self):
        rates = [r.rate_average for r in SiteAlbumReview.gql('WHERE album = :1', self).fetch(1000) if r.rate_average is not None]
        if len(rates):
            return sum(rates) / len(rates)

class SiteAlbumStar(CustomModel):
    "Хранит информацию о любимых альбомах пользователей."
    album = db.ReferenceProperty(SiteAlbum)
    user = db.UserProperty()
    added = db.DateTimeProperty(auto_now_add=True)

class SiteImage(CustomModel):
    album = db.ReferenceProperty(SiteAlbum)
    medium = db.LinkProperty()
    original = db.LinkProperty()
    type = db.StringProperty()

class SiteTrack(CustomModel):
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

class SiteFile(CustomModel):
    album = db.ReferenceProperty(SiteAlbum)
    name = db.StringProperty()
    uri = db.LinkProperty()
    type = db.StringProperty()
    size = db.IntegerProperty()

class SiteAlbumReview(CustomModel):
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

    def put(self):
        if self.author is None:
            self.author = get_current_user()
        self.rate_average = self.get_avg()
        return CustomModel.put(self)

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

class Event(CustomModel):
    lastfm_id = db.IntegerProperty()
    artist = db.ReferenceProperty(SiteArtist)
    title = db.StringProperty()
    date = db.DateTimeProperty()
    venue = db.StringProperty()
    city = db.StringProperty()
    url = db.LinkProperty()

class SiteAlbumLabel(CustomModel):
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
    user = db.UserProperty(required=_REQUIRED)
    # Дата установки, на всякий случай.
    published = db.DateTimeProperty(auto_now_add=True)


class File(CustomModel):
    id = db.IntegerProperty()
    file_key = db.StringProperty() # blobstore key
    owner = db.UserProperty()
    content_type = db.StringProperty()
    filename = db.StringProperty()
    creation = db.DateTimeProperty(auto_now_add=True)
    size = db.IntegerProperty() # file size in bytes
    duration = db.IntegerProperty() # in seconds
    published = db.BooleanProperty() # False to show to admins only
    album = db.ReferenceProperty(SiteAlbum) # album to which this file belongs to
    image_url = db.LinkProperty() # Picasa URL
    weight = db.IntegerProperty() # used for sorting
    song_artist = db.StringProperty()
    song_title = db.StringProperty()
    remixer = db.StringProperty()
    # The number of times this file was downloaded.
    download_count = db.IntegerProperty()
    # The number of bytes downloaded.
    download_bytes = db.IntegerProperty()

    def put(self):
        if not self.id:
            self.id = self.weight = nextId(File)
            logging.info('New file: %s (file/serve?id=%u)' % (self.filename, self.id))
        if not self.content_type:
            self.content_type = 'application/octet-stream'
        return CustomModel.put(self)


class DownloadTicket(CustomModel):
    created = db.DateTimeProperty(auto_now_add=True)
    activated = db.DateTimeProperty() # first access, used to block after 10 minutes
    email = db.EmailProperty()
    album_id = db.IntegerProperty()
    file_id = db.IntegerProperty()

    @classmethod
    def get_by_key(cls, key):
        return db.get(db.Key(key))


class Artist(CustomModel):
    # Отображаемое на сайте имя.
    name = db.StringProperty(required=_REQUIRED)
    # Имя, используемое для сортировки.  Всякие "the" из начала удаляются.
    sortname = db.StringProperty(required=False)
    # Имя, используемое в last.fm (может несоответствовать)
    lastfm_name = db.StringProperty()
    # Идентификатор в твиттере, если есть.
    twitter = db.StringProperty()
    # Адрес основного сайта.
    homepage = db.LinkProperty()
    # Адрес страницы в контакте
    vk = db.LinkProperty()
