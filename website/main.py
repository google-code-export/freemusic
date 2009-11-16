#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sts=2 sw=2 et:

# Python imports
import logging, pickle, os, urllib

# GAE imports
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

# Site imports.
import model

class BaseRequestHandler(webapp.RequestHandler):
  def render(self, template_name, vars={}, content_type='text/html'):
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, 'templates', template_name)

    result = template.render(path, vars)
    self.response.out.write(result)

  def quote(self, text):
    return urllib.quote(text.encode('utf8'))

  def unquote(self, text):
    return urllib.unquote(text).decode('utf8')


class MainHandler(BaseRequestHandler):
  def get(self):
    self.response.out.write('Hello world!')


class IndexHandler(BaseRequestHandler):
  def get(self):
    latest = model.SiteAlbum.all().fetch(10)
    self.render('index.html', {
      'albums': latest,
    })


class SubmitHandler(BaseRequestHandler):
  def get(self):
    self.render('submit.html')

  def post(self):
    artist = self.get_artist(self.request.get('artist'))
    album = self.get_album(self.request.get('album'), artist)

    logging.info('New album "%s" from %s' % (album.name, artist.name))
    next = '/music/' + self.quote(artist.name) + '/' + self.quote(album.name) + '/'
    self.redirect(next)

  def get_artist(self, name):
    artist = model.SiteArtist.gql('WHERE name = :1', name).get()
    if not artist:
      artist = model.SiteArtist(name=name)
      artist.put()
    return artist

  def get_album(self, name, artist):
    album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, name).get()
    if not album:
      album = model.SiteAlbum(name=name, artist=artist)
      album.put()
    return album


class AddFileHandler(BaseRequestHandler):
  @login_required
  def get(self):
    self.render('add-file.html', {
      'artist': self.request.get('artist'),
      'album': self.request.get('album'),
    })


class AlbumHandler(BaseRequestHandler):
  def get(self, artist_name, album_name):
    data = self.load(artist_name, album_name)
    self.render('view-album.html', data)

  def load(self, artist_name, album_name):
    artist = model.SiteArtist.gql('WHERE name = :1', self.unquote(artist_name)).get()
    if artist is None:
      raise Exception('No such artist.')

    album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, self.unquote(album_name)).get()
    if album is None:
      raise Exception('No such album.')

    data = {
      'artist': {
        'name': artist.name,
        },
      'album': {
        'name': album.name,
        'date': album.release_date,
        'rating': album.rating,
        'cover': album.cover_large,
        'tracks': [],
        'files': [],
        },
    }

    if album.tracks:
      data['album']['tracks'] = pickle.loads(album.tracks)
    if album.files:
      data['album']['files'] = pickle.loads(album.files)

    return data

class AdminInitHandler(BaseRequestHandler):
  @login_required
  def get(self):
    for tmp in model.SiteArtist.all().fetch(1000):
      tmp.delete()
    for tmp in model.SiteAlbum.all().fetch(1000):
      tmp.delete()

    data = {
      'artists': {
        'Skazka': {
          'albums': {
            'Fairy Tale': {
              'cover_small': 'http://ebm.net.ru/sites/default/files/6/66/1066/folder.jpg.thumbnail.jpg',
              'cover_large': 'http://ebm.net.ru/sites/default/files/6/66/1066/folder.jpg.medium.jpg',
              'tracks': [
                { 'title': 'Russian Field',
                  'number': 1,
                  'mp3': 'http://ebm.net.ru/download/1056/01%20Russian%20Field.mp3' },
                { 'title': 'Ocean',
                  'number': 2,
                  'mp3': 'http://ebm.net.ru/download/1057/02%20Ocean.mp3' },
                { 'title': 'Aurora Borealis',
                  'number': 3,
                  'mp3': 'http://ebm.net.ru/download/1058/03%20Aurora%20Borealis.mp3' },
                { 'title': 'Mountain River',
                  'number': 4,
                  'mp3': 'http://ebm.net.ru/download/1059/04%20Mountain%20River.mp3' },
                { 'title': 'Fairy Tale',
                  'number': 10,
                  'mp3': 'http://ebm.net.ru/download/1065/10%20Fairy%20Tale.mp3' },
                ],
              'files': [
                { 'url': 'http://ebm.net.ru/download/1067/skazka-2009-fairy-tale.zip',
                  'name': 'skazka-2009-fairy-tale.zip',
                  'type': 'application/zip' },
                { 'url': 'http://ebm.net.ru/download/1067/skazka-2009-fairy-tale.zip?torrent',
                  'name': 'skazka-2009-fairy-tale.zip.torrent',
                  'type': 'application/x-bit-torrent' },
                ],
              },
            },
          },
        },
    }

    for artist_name in data['artists']:
      artist_data = data['artists'][artist_name]
      artist = model.SiteArtist(name=artist_name)
      artist.put()

      for album_name in artist_data['albums']:
        album_data = artist_data['albums'][album_name]
        album = model.SiteAlbum(name=album_name,
          artist=artist)
        for k in album_data:
          if type(album_data[k]) == type({}) or type(album_data[k]) == type([]):
            setattr(album, k, pickle.dumps(album_data[k]))
          else:
            setattr(album, k, album_data[k])
        album.put()

    self.redirect('/')

def main():
  application = webapp.WSGIApplication([
    ('/', IndexHandler),
    ('/add/file', AddFileHandler),
    ('/submit', SubmitHandler),
    ('/music/([^/]+)/([^/]+)/', AlbumHandler),
    ('/admin/init', AdminInitHandler),
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
