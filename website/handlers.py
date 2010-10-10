# vim: set ts=4 sts=4 sw=4 et fileencoding=utf-8:

# Python imports.
import logging
import urllib
import urlparse
import os
import wsgiref.handlers

# GAE imports.
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from django.utils import simplejson

# Site imports.
import config
import model

class BaseHandler(webapp.RequestHandler):
    def getHost(self):
        url = urlparse.urlparse(self.request.url)
        return url[1]

    def getBaseURL(self):
        """
        Возвращает базовый адрес текущего сайта.
        """
        url = urlparse.urlparse(self.request.url)
        return url[0] + '://' + url[1] + '/'

    def get_styles(self, hostname):
        """
        Возвращает имена файлов со стилями. При работе в SDK возвращает
        отдельные стили из /static/styles/, в нормальном режиме — один
        готовый файл.
        """
        if hostname.endswith(':8080'):
            return sorted(['/static/styles/' + x for x in os.walk(os.path.join(os.path.dirname(__file__), 'static', 'styles')).next()[2]])
        else:
            return ['/static/styles.css']

    def get_scripts(self, hostname):
        """
        Возвращает имена файлов со скриптами. При работе в SDK возвращает
        отдельные стили из /static/scripts/, в нормальном режиме — один
        готовый файл.
        """
        if hostname.endswith(':8080'):
            return sorted(['/static/scripts/' + x for x in os.walk(os.path.join(os.path.dirname(__file__), 'static', 'scripts')).next()[2]])
        else:
            return ['/static/scripts.js']

    def render(self, template_name, vars=None, ret=False):
        """
        Вызывает указанный шаблон, возвращает результат.
        """
        vars = vars or dict()
        vars['base'] = self.getBaseURL()
        vars['self'] = self.request.uri
        vars['host'] = self.getHost()
        vars['styles'] = self.get_styles(vars['host'])
        vars['scripts'] = self.get_scripts(vars['host'])
        vars['logout_uri'] = users.create_logout_url(self.request.uri)
        vars['login_uri'] = users.create_login_url(self.request.uri)
        vars['is_admin'] = users.is_current_user_admin()
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 'templates', template_name)
        result = template.render(path, vars)
        if not ret:
            self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
            self.response.out.write(result)
        return result

    def send_text(self, text):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        self.response.out.write(text)


class AlbumHandler(BaseHandler):
    def get(self, album_id):
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        upload_url = blobstore.create_upload_url('/upload/callback?album=' + album_id)
        self.render('album.html', {
            'album': album,
            'files': model.File.gql('WHERE album = :1 ORDER BY weight', album).fetch(100),
            'upload_url': users.is_current_user_admin() and upload_url or None,
        })


class AlbumEditHandler(BaseHandler):
    def get(self):
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        self.render('album-edit.html', {
            'album': album,
        })

    def post(self):
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        album.name = self.request.get('name')
        album.cover_id = self.request.get('cover_id')
        if album.cover_id:
            album.cover_large = images.get_serving_url(album.cover_id)
            album.cover_small = album.cover_large + '=s200-c'

        album.put()
        self.redirect('/album/' + str(album.id))


class FileServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        blob_info = blobstore.BlobInfo.get(self.request.get('id'))
        self.send_blob(blob_info)


class IndexHandler(BaseHandler):
    """
    The main page of the web site.
    """
    count = 100

    def get(self):
        """
        Shows self.count recent albums.
        """
        self.render('index.html', {
            'albums': model.SiteAlbum.all().fetch(100),
            'labels': model.SiteAlbumLabel.all().order('label').fetch(100),
        })


class InitHandler(BaseHandler):
    """
    Creates some dummy albums for testing.
    """

    def get(self):
        self.__add_album(1, u'Repus Tuto Matos', u'Включи меня', [u'aggro-industrial', u'clean', u'vocals', u'remixes', u'russian lyrics', u'single'])
        self.__add_album(2, None, u'On The Parallel Front', [u'compilation', u'industrial', u'x-line'])
        self.__add_album(3, u'Tekkno Orgasm', u'Unreleased', [u'compilation', u'dance', u'industrial', u'male vocals', u'screaming', u'vocals', u'unreleased'])
        self.__add_album(4, u'Stompwork', u'Stomp The Streets', [u'dead channel', u'gabber', u'hardcore', u'industrial', u'instrumental'])
        self.send_text('OK')

    def __add_album(self, id, artist_name, title, labels):
        artist = model.SiteArtist.gql('WHERE name = :1', artist_name).get()
        if not artist:
            artist = model.SiteArtist(name=artist_name)
            artist.put()

        album = model.SiteAlbum.gql('WHERE id = :1', id).get()
        if album is None:
            album = model.SiteAlbum(id=id)
        album.artist = artist
        album.cover_large = 'http://freemusic.googlecode.com/hg/test-data/album/%02u/image-01-large.jpg' % id
        album.cover_small = 'http://freemusic.googlecode.com/hg/test-data/album/%02u/image-01-small.jpg' % id
        album.labels = labels
        album.owner = users.User('justin.forest@gmail.com')
        album.put()

        for label in labels:
            l = model.SiteAlbumLabel.gql('WHERE label = :1', label).get()
            if l is None:
                model.SiteAlbumLabel(label=label, user=album.owner, album=album).put()


class UploadHandler(BaseHandler):
    """
    Lets admins upload files.  One at a time and only manually.
    """
    def get(self):
        """
        Shows the form.
        """
        self.render('upload.html', {
            'action': blobstore.create_upload_url('/upload/callback?album=' + self.request.get('album')),
            'files': model.File.all().order('-id').fetch(100),
        })


class UploadCallbackHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        """
        Handles the callback.
        """
        files = self.get_uploads('file')
        blob = files[0]

        if self.request.get('album'):
            album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('album'))).get()
        else:
            album = None

        file = model.File()
        file.file_key = str(blob.key())
        file.owner = users.get_current_user()
        for k in ('content_type', 'filename', 'size', 'creation'):
            setattr(file, k, getattr(blob, k))
        file.published = True
        file.album = album
        if file.content_type.startswith('image/'):
            file.image_url = images.get_serving_url(file.file_key)
        file.put()

        if self.request.get('album'):
            self.redirect('/album/' + self.request.get('album'))
        else:
            self.redirect('/upload')


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        ('/', IndexHandler),
        ('/album/(\d+)$', AlbumHandler),
        ('/album/edit$', AlbumEditHandler),
        ('/file/serve', FileServeHandler),
        ('/init', InitHandler),
        ('/upload', UploadHandler),
        ('/upload/callback', UploadCallbackHandler),
    ], debug=config.DEBUG))
