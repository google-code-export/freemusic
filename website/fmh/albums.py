# vim: set fileencoding=utf-8:

from google.appengine.ext import webapp

from fmh import json
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


class View(view.Base):
    def render(self, album):
        data = {
            'album_id': album.id,
            'key': album.key(),
            'title': album.name,
            'artist_name': album.artists[0],
            'homepage': album.homepage,
            'download_link': album.download_link,
            'download_count': album.download_count,
        }
        super(View, self).render('albums/view.html', data)
