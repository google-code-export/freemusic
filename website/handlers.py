# vim: set ts=4 sts=4 sw=4 et fileencoding=utf-8:

# Python imports.
import logging
import urllib
import urlparse
import os
import os.path
import re
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

def get_all_labels():
    """
    Returns a list of all labels.  Uses memcache.
    """
    labels = memcache.get('all-labels')
    if not labels or type(labels) != list:
        labels = []
        for album in model.SiteAlbum.all().fetch(1000):
            for label in album.labels:
                if label not in labels:
                    labels.append(label)
        labels = sorted(labels)
        memcache.set('all-labels', labels)
    return labels


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
        self.render('album.html', {
            'album': album,
            'files': self._get_files(album),
            'compilation': 'compilation' in album.labels,
            'upload_url': self._get_upload_url(album, '/album/' + album_id),
        })

    def _get_upload_url(self, album, back=None):
        after = '/upload/callback?album=' + str(album.id)
        if back:
            after += '&back=' + urllib.quote(back)
        upload_url = blobstore.create_upload_url(after)
        return users.is_current_user_admin() and upload_url or None

    def _get_files(self, album):
        """
        Returns a dictionary with all album files.  Keys: images, tracks,
        other, all lists.  Tracks are dictionaries, other are models.
        """
        result = {
            'images': [],
            'tracks': [],
            'other': [],
        }
        files = [f for f in model.File.gql('WHERE album = :1 ORDER BY weight', album).fetch(100) if f.published]
        for file in files:
            if file.image_url:
                result['images'].append(file)
            elif file.content_type and file.content_type.startswith('audio/'):
                if file.content_type == 'audio/mp3':
                    track = {
                        'id': file.id,
                        'content_type': file.content_type,
                        'song_title': file.song_title or file.filename,
                        'song_artist': file.song_artist,
                        'duration': None,
                        'mp3_link': '/file/serve/%s/%s' % (file.id, file.filename),
                        'ogg_link': None,
                    }
                    if file.duration:
                        track['duration'] = '%u:%u' % (file.duration / 60, file.duration % 60)
                    ogg_name = os.path.splitext(file.filename)[0] + '.ogg'
                    for file in files:
                        if file.filename == ogg_name:
                            track['ogg_link'] = '/file/serve/%s/%s' % (file.id, file.filename)
                    result['tracks'].append(track)
            else:
                result['other'].append(file)
        return result


class AlbumDownloadHandler(AlbumHandler):
    """
    Shows files that can be downloaded.
    """
    def get(self, album_id):
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        self.render('album-download.html', {
            'album': album,
            'files': self._get_files(album),
            'upload_url': self._get_upload_url(album, '/album/%s/download' % album_id),
        })


class AlbumEditHandler(AlbumHandler):
    def get(self):
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        self.render('album-edit.html', {
            'album': album,
            'files': model.File.gql('WHERE album = :1 ORDER BY weight', album).fetch(100),
        })

    def post(self):
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        album.name = self.request.get('name')
        album.cover_id = self.request.get('cover_id')
        if album.cover_id:
            album.cover_large = images.get_serving_url(album.cover_id)
            album.cover_small = album.cover_large + '=s200-c'
            # ditch broken SDK URLs, use browser scaling
            if album.cover_small.startswith('http://0.0.0.0:'):
                album.cover_small = album.cover_large
        else:
            album.cover_id = None
            album.cover_large = None
            album.cover_small = None
        album.homepage = self.request.get('homepage') or None
        album.labels = [l for l in re.split(',\s+', self.request.get('labels')) if l.strip()]

        files = model.File.gql('WHERE album = :1', album).fetch(100)
        self.__update_files(files, 'file', { 'weight': int, 'song_title': unicode, 'song_artist': unicode, 'duration': int, 'filename': unicode, 'content_type': str, 'published': bool })

        # Find artists.
        album.artists = list(set([f.song_artist.strip() for f in files if f.song_artist]))

        album.put()
        self.redirect('/album/' + str(album.id))

    def __update_files(self, files, prefix, converters):
        for file in files:
            for key in converters.keys():
                fieldname = '%s.%s.%s' % (prefix, file.id, key)
                value = self.request.get(fieldname, None)
                logging.info('%s = %s' % (fieldname, value))
                if value is None:
                    pass
                elif not value:
                    setattr(file, key, None)
                else:
                    setattr(file, key, converters[key](self.request.get(fieldname)))
            if not self.request.get('%s.%s.published' % (prefix, file.id)):
                file.published = False
            file.put()


class AlbumSubmitHandler(BaseHandler):
    def get(self):
        self.render('album-submit.html')

    def post(self):
        album = model.SiteAlbum()
        album.name = self.request.get('name') or None
        album.homepage = self.request.get('homepage') or None
        album.labels = [l for l in re.split(',\s+', self.request.get('labels')) if l.strip()]
        album.put()
        self.redirect('/album/' + str(album.id))


class FileServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, file_id):
        file = model.File.gql('WHERE id = :1', int(file_id)).get()
        blob = blobstore.BlobInfo.get(file.file_key)
        self.send_blob(blob)


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
            'labels': get_all_labels(),
        })


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

        # If the album doesn't have a cover and we've just uploaded
        # an image, use it as the cover.
        if file.image_url and not (album.cover_id and album.cover_small and album.cover_large):
            album.cover_id = file.file_key
            album.cover_large = images.get_serving_url(album.cover_id)
            album.cover_small = album.cover_large + '=s200-c'
            # ditch broken SDK URLs, use browser scaling
            if album.cover_small.startswith('http://0.0.0.0:'):
                album.cover_small = album.cover_large
            album.put()

        if self.request.get('back'):
            self.redirect(self.request.get('back'))
        elif self.request.get('album'):
            self.redirect('/album/' + self.request.get('album'))
        else:
            self.redirect('/upload')


if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        ('/', IndexHandler),
        ('/album/(\d+)$', AlbumHandler),
        ('/album/(\d+)/download$', AlbumDownloadHandler),
        ('/album/edit$', AlbumEditHandler),
        ('/album/submit$', AlbumSubmitHandler),
        ('/file/serve/(\d+)/.+$', FileServeHandler),
        ('/upload', UploadHandler),
        ('/upload/callback', UploadCallbackHandler),
    ], debug=config.DEBUG))
