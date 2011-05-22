# vim: set fileencoding=utf-8:

from google.appengine.ext import webapp

from fmh import json
from fmh import mail
from fmh import model
from fmh import view


class EditController(webapp.RequestHandler):
    def get(self, album_id):
        EditView(self).render(model.SiteAlbum.get_by_id(int(album_id)))

    def post(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
        self.process_form(album)

    def process_form(self, album):
        album.name = self.request.get('title')
        album.artists = [ self.request.get('artist') ]
        album.homepage = self.request.get('homepage')
        album.download_link = self.request.get('download_link')
        album.cover_small = self.request.get('cover_small')
        album.put()
        self.redirect('/album/%u' % album.id)


class EditView(view.Base):
    def render(self, album):
        data = {
            'album_id': album.id,
            'album_key': album.key(),
            'title': album.name,
            'artist_name': album.artists[0],
            'homepage': album.homepage,
            'download_link': album.download_link,
            'cover_small': album.cover_small,
        }
        super(EditView, self).render('albums/edit.html', data)


class AddController(EditController):
    def get(self):
        view.Base(self).render('albums/add.html')

    def post(self):
        album = model.SiteAlbum()
        self.process_form(album)


class ViewController(webapp.RequestHandler):
    def get(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
        View(self).render(album)


class JSONController(webapp.RequestHandler):
    def get(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
        json.dump(self.response, album)


class DownloadController(webapp.RequestHandler):
    def get(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
        if not album.download_count:
            album.download_count = 0
        album.download_count += 1
        album.put()
        self.redirect(album.download_link)


class CoverController(webapp.RequestHandler):
    def get(self, album_id):
        # album = model.SiteAlbum.get_by_id(int(album_id))
        self.redirect('http://lh4.ggpht.com/32j3lgf9wPBsGHUjgwtyJyEzObEyVF7RwSEz4WABdNV6YP-AjrDKmhxyWiMTyYuIUoBMOn8nRMIKS09oKA=s200-c')


class ReviewController(webapp.RequestHandler):
    def post(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
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


class ListController(webapp.RequestHandler):
    def get(self):
        albums = model.SiteAlbum.find()
        ListView(self).render(albums)

class ListView(view.Base):
    def render(self, albums):
        super(ListView, self).render('albums/list.html', {
            'albums': albums,
        })
