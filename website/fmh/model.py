# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 et:

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


class SiteAlbum(CustomModel):
    id = db.IntegerProperty()
    name = db.StringProperty()
    text = db.TextProperty()
    artists = db.StringListProperty()
    release_date = db.DateProperty(auto_now_add=True)
    homepage = db.LinkProperty()
    download_link = db.LinkProperty()
    rating = db.RatingProperty()
    cover_id = db.StringProperty()
    cover_large = db.LinkProperty()
    cover_small = db.LinkProperty()
    labels = db.StringListProperty()
    owner = db.UserProperty()
    rate = db.RatingProperty()

    def put(self):
        if not self.id:
            last = SiteAlbum.all().order('-id').get()
            if last is None:
                self.id = 1
            else:
                self.id = last.id + 1
        return CustomModel.put(self)

    @classmethod
    def get_by_id(cls, album_id):
        return cls.gql('WHERE id = :1', album_id).get()


class SiteUser(CustomModel):
    user = db.UserProperty(required=_REQUIRED)
    joined = db.DateTimeProperty(auto_now_add=True)
    weight = db.FloatProperty()
    nickname = db.StringProperty()


class SiteAlbumStar(CustomModel):
    "Хранит информацию о любимых альбомах пользователей."
    album = db.ReferenceProperty(SiteAlbum)
    user = db.UserProperty()
    added = db.DateTimeProperty(auto_now_add=True)


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
    # Имена всех задействованных исполнителей, обновляются при сохранении,
    # используются для поиска.
    all_artists = db.StringListProperty()
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
        # Обновление списка исполнителей, для более простого поиска.
        self.all_artists = []
        if self.song_artist:
            self.all_artists.append(self.song_artist)
        if self.remixer and self.remixer not in self.all_artists:
            self.all_artists.append(self.remixer)
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
    """Описание исполнителя."""

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

    # Связанные артисты.
    related_artists = db.StringListProperty()

    # Количество альбомов, в которых задействован.
    track_count = db.IntegerProperty()

    # Почтовые адреса администраторов.
    admins = db.StringListProperty()

    def to_dict(self):
        return {
        'name': self.name,
        'sortname': util.mksortname(self.name),
        'lastfm_name': self.lastfm_name,
        'twitter': self.twitter,
        'homepage': self.homepage,
        'vk': self.vk,
        'related_artists': self.related_artists,
        }


class MLSubscriber(CustomModel):
    """Информация о подписчике на рассылку."""

    # Дата добавления в список (подтверждение).
    added = db.DateTimeProperty(auto_now_add=True)

    # Почтовый адрес (проверенный).
    email = db.EmailProperty()

    # Имя исполнителя.
    artist = db.StringProperty()


class MLMessage(CustomModel):
    """Сообщение для рассылки."""

    # Дата создания.  Обновляется при редактировании.  Фактически сообщение
    # отправляется через час после указанной здесь даты.
    created = db.DateTimeProperty(auto_now_add=True)

    # Адрес отправителя.
    sender = db.EmailProperty()

    # Имя исполнителя, в чью рассылку отправлено сообщение.
    artist = db.StringProperty()

    # Заголовок сообщения.
    subject = db.StringProperty()

    # Текст сообщения (сырой Markdown).
    text = db.TextProperty()

    # True если сообщение ушло и редактировать его нельзя.
    sent = db.BooleanProperty()