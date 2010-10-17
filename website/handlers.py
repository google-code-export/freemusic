# vim: set ts=4 sts=4 sw=4 et fileencoding=utf-8:

# Python imports.
import datetime
import logging
import urllib
import urlparse
import operator # for sorting
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

class NotFoundException(Exception): pass

def get_labels_from_albums(albums):
    labels = []
    for album in albums:
        for label in album['labels']:
            if label not in labels:
                labels.append(label)
    return sorted(labels)

def get_all_labels():
    """
    Returns a list of all labels.  Uses memcache.
    """
    labels = memcache.get('all-labels')
    if not labels or type(labels) != list:
        labels = get_labels_from_albums([l.dict() for l in model.SiteAlbum.all().fetch(1000)])
        memcache.set('all-labels', labels)
    return labels


class BaseHandler(webapp.RequestHandler):
    requireLogin = False
    requireAdmin = False
    # Page cache is enabled by default.
    cache_page = False
    cache_data = True
    # Default content type, used by render().  Subclasses can override this.
    content_type = 'text/html'

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
        if False and hostname.endswith(':8080'):
            return sorted(['/static/styles/' + x for x in os.walk(os.path.join(os.path.dirname(__file__), 'static', 'styles')).next()[2]])
        else:
            return ['/static/styles.css']

    def get_scripts(self, hostname):
        """
        Возвращает имена файлов со скриптами. При работе в SDK возвращает
        отдельные стили из /static/scripts/, в нормальном режиме — один
        готовый файл.
        """
        if False and hostname.endswith(':8080'):
            return sorted(['/static/scripts/' + x for x in os.walk(os.path.join(os.path.dirname(__file__), 'static', 'scripts')).next()[2]])
        else:
            return ['/static/scripts.js']

    def render(self, template_name, vars=None, ret=False):
        """
        Вызывает указанный шаблон, возвращает результат.
        """
        vars = vars or dict()
        if type(vars) != dict:
            raise Exception('%s.render() expects a dictionary!' % self.__class__.__name__)
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
        logging.debug('Rendering %s with %s' % (self.request.path, template_name))
        result = template.render(path, vars)
        if not ret:
            self.response.headers['Content-Type'] = self.content_type + '; charset=utf-8'
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
            cache_key = self.request.path + '#page'
            cached = memcache.get(self.request.path)
            use_cache = True
            if not self.cache_page:
                use_cache = False
                logging.debug('Cache MIS for \"%s\": disabled by class %s' % (cache_key, self.__class__.__name__))
            if use_cache and type(cached) != tuple:
                use_cache = False
                logging.debug('Cache MIS for \"%s\"' % cache_key)
            if use_cache and users.is_current_user_admin() and 'nocache' in self.request.arguments():
                logging.debug('Cache MIS for \"%s\": requested by admin' % cache_key)
                use_cache = False
            if not use_cache:
                self._real_get(*args)
                cached = (self.response.headers, self.response.out, )
                memcache.set(self.request.path, cached)
            else:
                logging.debug('Cache HIT for \"%s\"' % cache_key)
            self.response.headers = cached[0]
            self.response.out = cached[1]

    def _real_get(self, *args):
        """
        Calls the _get_data() method, which must return a dictionary to be used
        with render().  The dictionary must contain only simple data, not
        objects or models, otherwise caching will break up.
        """
        if not hasattr(self, '_get_data'):
            logging.error('Class %s does not define the _get_data() method, sending 501.' % self.__class__.__name__)
            self.error(501)
        else:
            cache_key = self.request.path + '#data'
            data = memcache.get(cache_key)
            use_cache = True
            if type(data) != dict:
                use_cache = False
                logging.debug('Cache MIS for "%s"' % cache_key)
            elif not self.cache_data:
                use_cache = False
                logging.debug('Cache IGN for "%s": disabled for class %s.' % (cache_key, self.__class__.__name__))
            elif users.is_current_user_admin() and 'nocache' in self.request.arguments():
                use_cache = False
                logging.debug('Cache IGN for "%s": requested by admin.' % (cache_key))
            if not use_cache:
                data = self._get_data(*args)
                if type(data) != dict:
                    logging.warning('%s._get_data() returned something other than a dictionary (%s), not caching.' % (self.__class__.__name__, data.__class__.__name__))
                else:
                    memcache.set(cache_key, data)
            else:
                logging.debug('Cache HIT for "%s"' % cache_key)
                # logging.debug(data)
            self.render(self.template, data)

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
        self.redirect(users.create_login_url(self.request.uri))
        return False

    def _reset_cache(self, uri):
        """
        Removes a page from cache, both data and the whole page.
        """
        memcache.delete(uri + '#data')
        memcache.delete(uri + '#page')


class AlbumHandler(BaseHandler):
    template = 'album.html'

    def _get_data(self, album_id):
        album = model.SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
        if album is None:
            raise NotFoundException('No such album.')
        files = self._get_files(album)
        artist = files['tracks'] and files['tracks'][0]['song_artist'] or None
        return {
            'album': album.dict(),
            'labels': sorted(album.labels),
            'artist': artist,
            'year': album.release_date.strftime('%Y'),
            'files': files,
            'compilation': 'compilation' in album.labels,
            'remixers': len([f for f in files['tracks'] if f['remixer']]),
        }

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
                link = self.getBaseURL() + 'file/%u/%s/%s' % (file.id, ticket.key(), urllib.quote(file.filename.encode('utf-8')))
                links.append(link)
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
                uri = '/file/%u/-/%s' % (file.id, file.filename)
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
        # Make sure the album exists.
        album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
        if album is None:
            raise NotFoundException('No such album.')
        # Сохраняем список исполнителей для обновления количества альбомов.
        old_artists = album.artists
        old_labels = album.labels
        # Обновление сведений об альбома.
        self.__update_album(album)
        # Обновление статистики исполнителей.
        self.__update_artist_counters(old_artists + album.artists)

        # Reset cache.
        self._reset_cache('/')
        self._reset_cache('/album/' + str(album.id))
        for label in list(set(old_labels + album.labels)):
            self._reset_cache('/tag/' + urllib.quote(label.encode('utf-8')))
        for artist in album.artists:
            self._reset_cache('/artist/' + urllib.quote(artist.encode('utf-8')))
        self._reset_cache('/artists')

        album.put()
        self.redirect('/album/' + str(album.id))

    def __update_album(self, album):
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
        album.labels = [l.strip() for l in re.split(',\s+', self.request.get('labels')) if l.strip()]

        files = model.File.gql('WHERE album = :1', album).fetch(100)
        self.__update_files(files, 'file', { 'weight': int, 'song_title': unicode, 'song_artist': unicode, 'duration': int, 'filename': unicode, 'content_type': str, 'published': bool, 'remixer': unicode })

        # Find artists.
        album.artists = self.__get_artists(album, files)

    def __update_artist_counters(self, artists):
        """
        Updates the track_count for all listed artists.
        """
        for artist_name in list(set(artists)):
            artist = model.Artist.gql('WHERE name = :1', artist_name).get()
            if artist is None:
                artist = model.Artist(name=artist_name)
            artist.track_count = model.File.gql('WHERE all_artists = :1', artist_name).count(100)
            artist.put()
            logging.debug('Artist "%s" now has %u tracks.' % (artist_name, artist.track_count))

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
        album.labels = [l.strip() for l in re.split(',\s+', self.request.get('labels')) if l.strip()]
        if self.request.get('release_date'):
            album.release_date = datetime.datetime.strptime(self.request.get('release_date'), '%Y-%m-%d').date()
        else:
            album.release_date = None
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


class FileServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """
    Serves a file.  Requires a ticket for large files.
    """
    def get(self, file_id, ticket_id, filename):
        file = model.File.gql('WHERE id = :1', int(file_id)).get()
        if file is None:
            raise NotFoundException('No such file.')
        if file.filename != filename.decode('utf-8'):
            raise NotFoundException('No file with such name.')
        if file.filename.endswith('.zip'):
            self.__check_ticket(file, ticket_id)
        blob = blobstore.BlobInfo.get(file.file_key)
        # Update statistics.
        if not file.download_count: file.download_count = 0
        if not file.download_bytes: file.download_bytes = 0
        file.download_count += 1
        file.download_bytes += blob.size
        file.put()
        # Send the file.
        self.send_blob(blob)

    def __check_ticket(self, file, ticket_id):
        """
        Makes sure that ticket_id is valid and the ticked did not expire yet.
        """
        ticket = model.DownloadTicket.get_by_key(ticket_id)
        if ticket is None:
            raise NotFoundException('Invalid download ticket.')
        now = datetime.datetime.now()
        if ticket.activated is None:
            ticket.activated = now
            ticket.put()
        elif (now - ticket.activated).seconds > 600:
            raise NotFoundException('This link is too old, please request a new one at http://www.freemusichub.net/album/%s' % (ticket.album_id))


class IndexHandler(BaseHandler):
    """
    The main page of the web site.
    """
    count = 100
    template = 'index.html'

    def _get_data(self, *args):
        albums = [a.dict() for a in self._get_albums(*args)]
        data = { 'albums': albums, 'labels': get_labels_from_albums(albums), }
        data.update(self._get_extra_data(*args))
        return data

    def _get_albums(self):
        """
        Returns albums (models) to show, filtered by whatever you need.
        """
        return model.SiteAlbum.all().order('-release_date').fetch(self.count)

    def _get_extra_data(self, *args):
        return {
            'labels': get_all_labels(),
        }


class IndexFeedHandler(IndexHandler):
    template = 'index.rss'
    content_type = 'text/xml'


class ArtistHandler(IndexHandler):
    template = 'artist.html'

    def _get_albums(self, artist_name):
        artist_name = urllib.unquote(artist_name).decode('utf-8')
        return model.SiteAlbum.gql('WHERE artists = :1 ORDER BY release_date DESC', artist_name).fetch(100)

    def _get_extra_data(self, artist_name):
        data = {'artist_name': urllib.unquote(artist_name).decode('utf-8')}
        artist = model.Artist.gql('WHERE name = :1', artist_name).get()
        if artist:
            data['artist'] = artist.to_dict()
        return data


class ArtistFeedHandler(ArtistHandler):
    template = 'artist.rss'
    content_type = 'text/xml'


class EditArtistHandler(BaseHandler):
    def get(self, name):
        artist = self.__get_artist(name)
        self.render('artist-edit.html', {
            'artist': artist,
        })

    def post(self, name):
        destination = '/artist/' + name
        artist = self.__get_artist(name)
        for k in ('lastfm_name', 'twitter', 'homepage', 'vk'):
            v = self.request.get(k)
            logging.info('%s = %s' % (k, v))
            setattr(artist, k, v or None)
        artist.related_artists = list(set(sorted([name.strip() for name in self.request.get('related_artists').split(',') if name.strip()])))
        if self.request.get('delete'):
            artist.delete()
            destination = '/artists'
        else:
            artist.put()

        # Reset cache.
        self._reset_cache('/artist/' + name)
        self._reset_cache('/artist/' + name + '/rss')
        self._reset_cache('/artists')

        self.redirect(destination)

    def __get_artist(self, quoted_name):
        name = urllib.unquote(quoted_name).strip().decode('utf-8')
        artist = model.Artist.gql('WHERE name = :1', name).get()
        if artist is None:
            artist = model.Artist(name=name)
        return artist


class ArtistsHandler(BaseHandler):
    """
    Displays the list of all artists.  If an admin adds ?gen&nocache to the URL, a fake
    list of artists will be generated for testing purposes.
    """
    template = 'artists.html'

    def _get_data(self):
        # Get a simple list of artists.
        if users.is_current_user_admin() and 'gen' in self.request.arguments():
            artists = self.__gen_artists()
        else:
            artists = self.__get_artists()
        total_count = len(artists)

        # Group by letters.
        letters = self.__split_by_letter(artists)

        # Group by columns.
        columns = self.__split_by_columns(letters, total_count)

        return {
            'columns': columns,
        }

    def __gen_artists(self):
        import random
        artists = dict()
        for idx in range(random.randrange(50)):
            letter = chr(random.randrange(ord('A'), ord('Z') + 1))
            name = letter + str(random.randrange(1000, 10000))
            artists[name] = {
                'name': name,
                'sortname': name,
                'id': random.randrange(1000),
            }
        return artists

    def __get_artists(self):
        """
        Returns all artists that have tracks.
        """
        artists = dict()
        for artist in model.Artist.gql('WHERE track_count > 0').fetch(1000):
            artists[artist.name] = artist.to_dict()
        return artists

    def __split_by_letter(self, artists):
        letters = {}
        for k in artists:
            artist = artists[k]
            letter = artist['sortname'][0].upper()
            if not letters.has_key(letter):
                letters[letter] = {'letter':letter, 'artists':[]}
            letters[letter]['artists'].append(artist)
        return sorted(letters.values(), cmp=lambda a, b: cmp(a['letter'], b['letter']))

    def __split_by_columns(self, letters, total_count):
        columns = []
        column = []
        per_column = total_count / 3
        column_size = 0

        for letter in letters:
            column.append(letter)
            column_size += len(letter['artists'])
            if column_size >= per_column and len(columns) < 2:
                columns.append(column)
                column = []
                column_size = 0

        if len(column):
            columns.append(column)

        return columns

    def __mksortname(self, name):
        name = unicode(name).lower()
        name = re.sub('[-_/\s.]+', ' ', name)
        name = re.sub(re.compile('[^\w\s]', re.U), u'', name)
        for prefix in (u'a', u'the'):
            if name.startswith(prefix + u' '):
                name = name[len(prefix)+1:] + u', ' + prefix
        return name


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
    template = 'tag.html'

    def _get_albums(self, tag):
        tag = urllib.unquote(tag).decode('utf-8')
        return model.SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', tag).fetch(100)

    def _get_extra_data(self, tag):
        return {
            'tag': urllib.unquote(tag).decode('utf-8'),
        }


class TagFeedHandler(TagHandler):
    template = 'tag.rss'
    content_type = 'text/xml'


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


class ZzzHandler(BaseHandler):
    def get(self):
        if not users.is_current_user_admin():
            raise Exception('Restricted area.')
        artists = []
        for file in model.File.all().fetch(1000):
            if self.request.get('action') == 'update-files':
                file.put()
            artists += file.all_artists
        if self.request.get('action') == 'update-artists':
            for artist_name in list(set(artists)):
                artist = model.Artist.gql('WHERE name = :1', artist_name).get()
                if artist is None:
                    artist = model.Artist(name=artist_name)
                artist.track_count = model.File.gql('WHERE all_artists = :1', artist_name).count(100)
                artist.put()
        self.send_text('OK')


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
        ('/artist/([^/]+)/rss$', ArtistFeedHandler),
        ('/artists', ArtistsHandler),
        ('/file/(\d+)/([^/]+)/(.+)$', FileServeHandler),
        ('/robots.txt$', RobotsHandler),
        ('/rss$', IndexFeedHandler),
        ('/sitemap.xml$', SiteMapHandler),
        ('/tag/([^/]+)$', TagHandler),
        ('/tag/([^/]+)/rss$', TagFeedHandler),
        ('/upload', UploadHandler),
        ('/upload/callback', UploadCallbackHandler),
        ('/zzz', ZzzHandler),
    ], debug=config.DEBUG))
