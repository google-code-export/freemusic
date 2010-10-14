# vim: set ts=4 sts=4 sw=4 et fileencoding=utf-8:

# Python imports.
import datetime
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
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from django.utils import simplejson

# Site imports.
import config
import model

class BreakRequestHandlingException(Exception): pass

def get_labels_from_albums(albums):
    labels = []
    for album in albums:
        for label in album.labels:
            if label not in labels:
                labels.append(label)
    return sorted(labels)

def get_all_labels():
    """
    Returns a list of all labels.  Uses memcache.
    """
    labels = memcache.get('all-labels')
    if not labels or type(labels) != list:
        labels = get_labels_from_albums(model.SiteAlbum.all().fetch(1000))
        memcache.set('all-labels', labels)
    return labels


class BaseHandler(webapp.RequestHandler):
    requireLogin = False
    requireAdmin = False
    cache = True

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
        vars['class_name'] = self.__class__.__name__
        vars['user'] = users.get_current_user()
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

    def handle_exception(self, e, debug_mode):
        if type(e) != BreakRequestHandlingException:
            webapp.RequestHandler.handle_exception(self, e, debug_mode)

    def get(self, *args):
        """
        Adds transparent caching to GET request handlers.  Real work is done by
        the _real_get() method.  Uses the URL as the cache key.  Cache hits and
        misses are logged to the DEBUG facility.
        """
        if not hasattr(self, '_real_get'):
            logging.error('Class %s does not define the _real_get() method, sending 501.' % self.__class__.__name__)
            self.error(501)
        else:
            cached = memcache.get(self.request.uri)
            if not self.cache or type(cached) != tuple:
                if not self.cache:
                    logging.debug('Cache MISS (disabled) for %s' % self.request.uri)
                else:
                    logging.debug('Cache MISS for %s' % self.request.uri)
                self._real_get(*args)
                cached = (self.response.headers, self.response.out, )
                memcache.set(self.request.uri, cached)
            else:
                logging.debug('Cache HIT for %s' % self.request.uri)
            self.response.headers = cached[0]
            self.response.out = cached[1]

    def post(self, *args):
        """
        Calls the _real_post() method, then flushes the page cache.
        """
        if not hasattr(self, '_real_post'):
            logging.error('Class %s does not define the _real_post() method, sending 501.' % self.__class__.__name__)
            self.error(501)
        else:
            self._real_post(*args)
            logging.debug('Cache DELETE for %s' % self.request.uri)
            memcache.delete(self.request.uri)

    def _check_admin(self, message):
        if users.is_current_user_admin():
            return True
        if self.request.method == 'POST':
            raise Exception(message)
        self.redirect(users.create_login_url(self.requrest.uri))
        return False


class AlbumHandler(BaseHandler):
    def _real_get(self, album_id):
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        files = self._get_files(album)
        artist = files['tracks'] and files['tracks'][0]['song_artist'] or None
        self.render('album.html', {
            'album': album,
            'labels': sorted(album.labels),
            'artist': artist,
            'year': album.release_date.strftime('%Y'),
            'files': files,
            'compilation': 'compilation' in album.labels,
            'remixers': len([f for f in files['tracks'] if f['remixer']]),
            'upload_url': self._get_upload_url(album, '/album/' + album_id),
        })

    def post(self, album_id):
        """
        Processes download requests.  Sends the user an email with the links.
        For each link there is a unique download ticket created.
        """
        links = []
        email = self.request.get('email')
        if not email:
            raise Exception('Not a valid email.')
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        if album is None:
            raise Exception(u'Нет такого альбома.')
        for file_id in self.request.get_all('id'):
            file = model.File.gql('WHERE id = :1', int(file_id)).get()
            if file is not None:
                ticket = model.DownloadTicket(email=email, album_id=int(album_id), file_id=int(file_id), used=False)
                ticket.put()
                links.append(self.getBaseURL() + 'download/' + str(ticket.key()) + '/' + file.filename.encode('utf-8'))
        if not links:
            raise Exception('No file selected.')
        data = {'email': email, 'links': links, 'album': album}
        html = self.render('download.html', data, ret=True)
        text = self.render('download.txt', data, ret=True)
        subject = u'Ссылки для скачивания альбома «%s»' % album.name
        mail.send_mail(sender=config.MAIL_FROM, to=email, bcc=config.MAIL_FROM, subject=subject, body=text, html=html)
        self.send_text(u'Ссылки отправлены на указанный почтовый адрес.')

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
        files = [f for f in model.File.gql('WHERE album = :1 ORDER BY weight', album).fetch(100) if f.published]
        result = {
            'images': self.__get_images(files),
            'tracks': self.__get_tracks(files),
            'other': self.__get_other(files),
        }
        return result

    def __get_images(self, files):
        return [f for f in files if f.image_url]

    def __get_tracks(self, files):
        tracks = dict()
        for file in files:
            if file.content_type.startswith('audio/'):
                key = os.path.splitext(file.filename)[0]
                if not tracks.has_key(key):
                    tracks[key] = {'id': file.id, 'weight': file.weight}
                tracks[key].update({
                    'song_title': file.song_title,
                    'song_artist': file.song_artist,
                    'remixer': file.remixer,
                    'duration': file.duration,
                })
                uri = '/file/serve/%s/%s' % (file.id, file.filename)
                if file.content_type == 'audio/mp3':
                    tracks[key]['mp3_link'] = uri
                elif file.content_type == 'audio/ogg':
                    tracks[key]['ogg_link'] = uri
        return sorted(tracks.values(), cmp=lambda a, b: int(a['weight'] - b['weight']))

    def __get_other(self, files):
        return [f for f in files if not f.image_url and not f.content_type.startswith('audio/')]


class AlbumDownloadHandler(AlbumHandler):
    """
    Shows files that can be downloaded.
    """
    def _real_get(self, album_id):
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        self.render('album-download.html', {
            'album': album,
            'files': self._get_files(album),
            'upload_url': self._get_upload_url(album, '/album/%s/download' % album_id),
        })


class AlbumEditHandler(AlbumHandler):
    def get(self):
        self._check_admin('Only admins can edit albums.')
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        self.render('album-edit.html', {
            'album': album,
            'files': model.File.gql('WHERE album = :1 ORDER BY weight', album).fetch(100),
        })

    def post(self):
        self._check_admin('Only admins can edit albums.')
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
        if self.request.get('release_date'):
            album.release_date = datetime.datetime.strptime(self.request.get('release_date'), '%Y-%m-%d').date()
        else:
            album.release_date = None
        album.labels = [l for l in re.split(',\s+', self.request.get('labels')) if l.strip()]

        files = model.File.gql('WHERE album = :1', album).fetch(100)
        self.__update_files(files, 'file', { 'weight': int, 'song_title': unicode, 'song_artist': unicode, 'duration': int, 'filename': unicode, 'content_type': str, 'published': bool, 'remixer': unicode })

        # Find artists.
        album.artists = self.__get_artists(album, files)

        album.put()
        self.redirect('/album/' + str(album.id))

    def __get_artists(self, album, files):
        artists = []
        for f in files:
            if f.song_artist:
                artists.append(f.song_artist.strip())
            if f.remixer:
                artists.append(f.remixer.strip())
        return list(set(artists))

    def __update_files(self, files, prefix, converters):
        for file in files:
            for key in converters.keys():
                fieldname = '%s.%s.%s' % (prefix, file.id, key)
                value = self.request.get(fieldname, None)
                logging.debug('%s = %s' % (fieldname, value))
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
        self._check_admin('Only admins can add albums.')
        self.render('album-submit.html')

    def post(self):
        self._check_admin('Only admins can add albums.')
        album = model.SiteAlbum()
        album.name = self.request.get('name') or None
        album.homepage = self.request.get('homepage') or None
        album.labels = [l for l in re.split(',\s+', self.request.get('labels')) if l.strip()]
        album.put()
        self.redirect('/album/' + str(album.id))


class AlbumUploadHandler(BaseHandler):
    """
    Returns an HTML form used for uploading a file.
    """
    def get(self, album_id):
        self._check_admin('Only admins can upload files.')
        upload_url = blobstore.create_upload_url('/upload/callback?album=%s' % album_id)
        self.render('album-upload.html', {
            'album_id': album_id,
            'upload_url': upload_url,
        })


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, ticket_key, filename):
        ticket = model.DownloadTicket.get_by_key(ticket_key)
        if ticket is None:
            raise Exception('No such ticket.')
        file = model.File.gql('WHERE id = :1', ticket.file_id).get()
        if file is None:
            raise Exception('File does not exist.')
        if file.filename != filename:
            raise Exception('File does not exist.')
        now = datetime.datetime.now()
        if ticket.activated is None:
            ticket.activated = now
            ticket.put()
        elif (now - ticket.activated).seconds > 6:
            raise Exception('This link is too old, please request a new one at http://www.freemusichub.net/album/%s' % (ticket.album_id))
        blob = blobstore.BlobInfo.get(file.file_key)
        self.send_blob(blob)


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

    def _real_get(self):
        """
        Shows self.count recent albums.
        """
        self._send_albums(model.SiteAlbum.all().order('-release_date').fetch(100))

    def _send_albums(self, albums, attrs=None):
        if not users.is_current_user_admin():
            albums = [a for a in albums if a.cover_small]
        attrs = attrs or dict()
        attrs.update({
            'albums': albums,
        })
        if not attrs.has_key('labels'):
            attrs['labels'] = get_all_labels()
        self.render('index.html', attrs)


class ArtistHandler(IndexHandler):
    """
    Shows albums by an artist.
    """
    def _real_get(self, artist_name):
        artist_name = urllib.unquote(artist_name).strip().decode('utf-8')
        artist = model.Artist.gql('WHERE name = :1', artist_name).get()
        albums = model.SiteAlbum.gql('WHERE artists = :1 ORDER BY release_date DESC', artist_name).fetch(100)
        self._send_albums(albums, {
            'artist': artist,
            'artist_name': artist_name,
            'labels': get_labels_from_albums(albums),
        })


class EditArtistHandler(BaseHandler):
    def get(self, name):
        artist = self.__get_artist(name)
        self.render('artist-edit.html', {
            'artist': artist,
        })

    def post(self, name):
        artist = self.__get_artist(name)
        for k in ('lastfm_name', 'twitter', 'homepage', 'vk'):
            v = self.request.get(k)
            logging.info('%s = %s' % (k, v))
            setattr(artist, k, v or None)
        artist.put()
        self.redirect('/artist/' + name)

    def __get_artist(self, quoted_name):
        name = urllib.unquote(quoted_name).strip().decode('utf-8')
        artist = model.Artist.gql('WHERE name = :1', name).get()
        if artist is None:
            artist = model.Artist(name=name)
        return artist


class ArtistsHandler(BaseHandler):
    """
    Displays the list of all artists.
    """
    def _real_get(self):
        total_count = 0.0
        stats = dict()
        # calculate counts
        tracks = model.File.all().fetch(1000)
        for track in tracks:
            for name in (track.song_artist, track.remixer):
                if name:
                    if not stats.has_key(name):
                        stats[name] = 0
                    stats[name] += 1
                    total_count += 1

        # calculate weight
        for name in stats:
            stats[name] = int(stats[name] * 10 / total_count)

        artists = [{'name': name, 'weight': stats[name]} for name in sorted(stats.keys())]
        self.render('artists.html', {
            'artists': artists,
        })


class RobotsHandler(BaseHandler):
    """
    Returns a robots.txt file which lists the sitemap.
    """
    def get(self):
        content = "Sitemap: %ssitemap.xml\n" % self.getBaseURL()
        content += "User-agent: *\n"
        content += "Disallow: /static/\n"
        self.send_text(content)


class SiteMapHandler(BaseHandler):
    """
    Returns a sitemap with links to all interesting pages.
    """
    def _real_get(self):
        content = '<?xml version="1.0" encoding="utf-8"?>\n'
        content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        base = self.getBaseURL()
        for album in model.SiteAlbum.all().order('-id').fetch(1000):
            content += "<url><loc>%salbum/%u</loc></url>\n" % (base, album.id)
        content += "</urlset>"
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(content)


class TagHandler(IndexHandler):
    """
    Shows albums tagged with a certain tag.
    """
    def _real_get(self, tag):
        tag = urllib.unquote(tag).strip().decode('utf-8')
        albums = model.SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', tag).fetch(100)
        self._send_albums(albums, {
            'tag': tag,
            'labels': [x for x in get_labels_from_albums(albums) if x != tag],
        })


class UploadHandler(BaseHandler):
    """
    Lets admins upload files.  One at a time and only manually.
    """
    def get(self):
        """
        Shows the form.
        """
        self._check_admin('Only admins can upload files.')
        self.render('upload.html', {
            'action': blobstore.create_upload_url('/upload/callback?album=' + self.request.get('album')),
            'files': model.File.all().order('-id').fetch(100),
        })


class UploadCallbackHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        """
        Handles the callback.
        """
        if self.request.get('album'):
            album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('album'))).get()
        else:
            album = None

        for blob in self.get_uploads('file'):
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
    if config.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    webapp.template.register_template_library('filters')
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        ('/', IndexHandler),
        ('/album/(\d+)$', AlbumHandler),
        ('/album/(\d+)/download$', AlbumDownloadHandler),
        ('/album/(\d+)/upload$', AlbumUploadHandler),
        ('/album/edit$', AlbumEditHandler),
        ('/album/submit$', AlbumSubmitHandler),
        ('/artist/([^/]+)$', ArtistHandler),
        ('/artist/([^/]+)/edit$', EditArtistHandler),
        ('/artists', ArtistsHandler),
        ('/download/([^/]+)/([^/]+)$', DownloadHandler),
        ('/file/serve/(\d+)/.+$', FileServeHandler),
        ('/robots.txt$', RobotsHandler),
        ('/sitemap.xml$', SiteMapHandler),
        ('/tag/([^/]+)$', TagHandler),
        ('/upload', UploadHandler),
        ('/upload/callback', UploadCallbackHandler),
    ], debug=config.DEBUG))
