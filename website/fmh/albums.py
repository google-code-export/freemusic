# vim: set fileencoding=utf-8:

from google.appengine.ext import webapp

from fmh import model
from fmh import view


class AddController(webapp.RequestHandler):
    def get(self):
        view.Base(self).render('albums/add.html')

    def post(self):
        album = model.SiteAlbum()
        album.name = self.request.get('title')
        album.artists = [ self.request.get('artist') ]
        album.homepage = self.request.get('homepage')
        album.download_link = self.request.get('download_link')
        album.put()
        self.redirect('/album/%u' % album.id)


class ViewController(webapp.RequestHandler):
    def get(self, album_id):
        album = model.SiteAlbum.get_by_id(int(album_id))
        View(self).render(album)


class View(view.Base):
    def render(self, album):
        data = {
            'id': album.id,
            'key': album.key(),
            'title': album.name,
            'artist_name': album.artists[0],
            'homepage': album.homepage,
            'download_link': album.download_link,
        }
        super(View, self).render('albums/view.html', data)
