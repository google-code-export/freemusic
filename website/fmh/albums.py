# vim: set fileencoding=utf-8:

import logging
import traceback

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import webapp

from fmh import json
from fmh import mail
from fmh import model
from fmh import view


class RequestHandler(webapp.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(RequestHandler, self).handle_exception(exception, debug_mode)
        logging.error('%s\n%s' % (exception, traceback.format_exc(exception)))
        view.Error(self).render(500)


class EditController(RequestHandler):
    def get(self, album_id):
        EditView(self).render(model.Album.get_by_id(int(album_id)))

    def post(self, album_id):
        album = model.Album.get_by_id(int(album_id))
        self.process_form(album)

    def process_form(self, album):
        album.artists = [ self.request.get('artist') ]
        self.set_value(album, 'title', 'name')
        self.set_value(album, 'homepage')
        self.set_value(album, 'download_link')
        self.set_value(album, 'cover_small', 'cover')
        self.set_value(album, 'owner', cls=users.User)
        album.put()
        self.redirect('/album/%u' % album.id)

    def set_value(self, album, k, k1=None, cls=unicode):
        value = self.request.get(k)
        if value:
            setattr(album, k1 or k, cls(value))


class EditView(view.Base):
    def render(self, album):
        data = {
            'album_id': album.id,
            'title': album.title,
            'artist_name': album.artist,
            'homepage': album.homepage,
            'download_link': album.download_link,
            'cover_small': album.cover,
        }
        super(EditView, self).render('albums/edit.html', data)


class AddController(EditController):
    def get(self):
        view.Base(self).render('albums/add.html')

    def post(self):
        album = model.Album()
        self.process_form(album)


class ViewController(RequestHandler):
    def get(self, album_id):
        album = model.Album.get_by_id(int(album_id))
        View(self).render(album)


class JSONController(RequestHandler):
    def get(self, album_id):
        album = model.Album.get_by_id(int(album_id))
        json.dump(self.response, album)


class DownloadController(RequestHandler):
    def get(self, album_id):
        album = model.Album.get_by_id(int(album_id))
        if not album.download_count:
            album.download_count = 0
        album.download_count += 1
        album.put()
        self.redirect(album.download_link)


class CoverController(RequestHandler):
    def get(self, album_id):
        # album = model.Album.get_by_id(int(album_id))
        self.redirect('http://lh4.ggpht.com/32j3lgf9wPBsGHUjgwtyJyEzObEyVF7RwSEz4WABdNV6YP-AjrDKmhxyWiMTyYuIUoBMOn8nRMIKS09oKA=s200-c')


class ReviewController(RequestHandler):
    def post(self, album_id):
        album = model.Album.get_by_id(int(album_id))
        review = album.add_review(self.request.get('email'),
            self.request.get('comment'),
            self.request.get('likes'))
        mail.send(review.author.email(), 'albums/review-confirm.html', {
            'review': review,
        })
        self.redirect('/album/%u' % album.id)

    def get(self, album_id):
        review = model.Review.get_by_key(self.request.get('confirm'))
        review.set_valid()
        self.redirect('/album/%u' % review.album.id)


class View(view.Base):
    def render(self, album):
        data = {
            'album': album,
            'reviews': model.Review.find_by_album(album),
        }
        super(View, self).render('albums/view.html', data)


class ListController(RequestHandler):
    def get(self):
        albums = model.Album.find()
        ListView(self).render(albums)

class ListView(view.Base):
    def render(self, albums, title=None):
        super(ListView, self).render('albums/list.html', {
            'albums': albums,
            'title': title,
        })


class BestController(RequestHandler):
    def get(self):
        albums = model.Album.find_best()
        ListView(self).render(albums, title=u'Лучшие альбомы')


class NewController(RequestHandler):
    def get(self):
        albums = model.Album.find_new()
        ListView(self).render(albums, title=u'Новые альбомы')


class UpgradeController(RequestHandler):
    def get(self):
        for old in model.SiteAlbum.find_all():
            taskqueue.add(url='/album/upgrade', params={ 'key': old.id })
        self.response.out.write('OK')

    def post(self):
        album_id = int(self.request.get('key'))
        old = model.SiteAlbum.get_by_id(album_id)
        album = model.Album()
        album.id = old.id
        album.title = old.name
        if old.artists:
            album.artist = old.artists[0]
        album.description = old.text
        album.date_released = old.release_date
        album.homepage = old.homepage
        album.download_link = old.download_link
        album.download_count = old.download_count
        album.cover = old.cover_large
        album.labels = old.labels
        album.owner = old.owner
        album.positive_reviews = old.positive_reviews

        for file in old.find_files('application/'):
            album.download_link = '/file/%s/%s' % (file.key(), file.filename)
            album.download_count = file.download_count
            break
        album.put()
