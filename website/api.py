# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# Python imports
import datetime, logging
from xml.dom.minidom import parseString

# GAE imports
from google.appengine.api import users
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db

# Local imports
import myxml, model
from base import BaseRequestHandler, HTTPException
from s3 import S3File, sign
import mail
import util

class APIRequest(BaseRequestHandler):
	def check_access(self, text):
		if not self.is_admin() and self.request.get('signature') != sign(text):
			self.force_admin()

	def reply(self, dict):
		self.sendXML(myxml.em(u'response', dict))

	def Xhandle_exception(self, e, debug_mode):
		if hasattr(e, 'status'):
			self.error(e.status)
		else:
			self.error(500)
		self.sendText(type(e).__name__ + ': ' + unicode(e) + u'\n')

class Index(APIRequest):
	def get(self):
		self.force_admin()
		self.sendAny('text/html', self.render('api.html'))

class Queue(BaseRequestHandler):
	def get(self):
		if self.request.path == '/api/queue.yaml':
			return self.get_yaml()
		xml = u''
		for file in S3File.all().fetch(1000):
			if not file.uri:
				file.uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			xml += myxml.em(u'file', {
				'name': file.name,
				'owner': file.owner,
				'uri': file.uri,
			})
		self.sendXML(myxml.em(u'queue', content=xml))

	def get_yaml(self):
		yaml = u''
		for file in S3File.all().fetch(1000):
			uri = file.uri
			if not uri and file.bucket and file.path:
				uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			yaml += u'- uri: %s\n' % uri
			if file.owner:
				yaml += u'  owner: %s\n' % file.owner
		if not yaml:
			yaml = u'# nothing to do'
		self.sendText(yaml)


class Delete(APIRequest):
	def get(self):
		url = self.request.get('url')
		if not url:
			raise HTTPException(400, u'Не указан URL удаляемого файла.')
		self.check_access(url)
		file = S3File.gql('WHERE uri = :1', url).get()
		if not file:
			raise HTTPException(404, u'Такого файла в очереди нет.')
		file.delete()
		self.redirect('/api/queue.xml')

class SubmitAlbum(APIRequest):
	def get(self):
		url = self.request.get('url')
		if not url:
			raise HTTPException(400, u'Не указан URL файла album.xml.')
		self.check_access(url)

		data = fetch(url)
		if data.status_code == 200:
			logging.info('New submission: ' + url)
			logging.debug(data.content)
			data = self.xml_to_dict(parseString(data.content), '/'.join(url.split('/')[0:-1]) + '/')
			data['album_xml'] = url
			logging.debug(data)
			if data:
				self.importAlbum(data)

	def importAlbum(self, data):
		keys = [] # ключи создаваемых объектов для удаления в случае исключения
		user = users.get_current_user()
		try:
			artist = model.SiteArtist.gql('WHERE sortname = :1', util.mksortname(data['artist'])).get()
			if not artist:
				artist = model.SiteArtist(name=data['artist'])
				keys.append(artist.put(quick=True))

			album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, data['name']).get()
			if album is not None and not self.request.get('replace'):
				raise HTTPException(400, u'Альбом "%s" от %s уже есть.' % (album.name, artist.name))
			if not album:
				album = model.SiteAlbum(artist=artist, name=data['name'], owner=users.User(data['owner']))
			if data['pubDate']:
				album.release_date = datetime.datetime.strptime(data['pubDate'][:10], '%Y-%m-%d').date()
			keys.append(album.put(quick=True))

			self.purge(model.SiteImage, album)
			for image in data['images']:
				keys.append(model.SiteImage(album=album, medium=image['medium'], original=image['original'], type=image['type']).put())

			self.purge(model.SiteTrack, album)
			for track in data['tracks']:
				keys.append(model.SiteTrack(album=album, title=track['title'], number=track['number'], mp3_link=track['mp3-link'], ogg_link=track['ogg-link'], duration=track['duration']).put())

			self.purge(model.SiteFile, album)
			for file in data['files']:
				keys.append(model.SiteFile(album=album, name=file['name'], uri=file['uri'], type=file['type'], size=file['size']).put())

			keys.append(album.put())
			artist.put() # обновление XML

			if user and data['owner'] != user.email():
				try:
					mail.send(data['owner'], self.render('album-added.html', {
						'album_id': album.id,
						'album_name': album.name,
					}))
				except KeyError:
					pass
		except Exception, e:
			db.delete(keys)
			raise

		if user:
			self.redirect('/album/' + str(album.id))
		else:
			self.sendXML(myxml.em(u'response', {
				'status': 'ok',
				'message': u'Album "%s" from %s is available at %s' % (album.name, artist.name, self.getBaseURL() + 'album/' + str(album.id)),
			}))

	def purge(self, source, album):
		old = source.gql('WHERE album = :1', album).fetch(1000)
		if old:
			db.delete(old)

	def xml_to_dict(self, xml, base_url):
		"""
		Преобразовывает содержимое album.xml в удобоваримый словарь.
		"""
		for em in xml.getElementsByTagName('album'):
			album = {
				'name': None,
				'artist': None,
				'pubDate': None,
				'owner': None,
				'images': [],
				'tracks': [],
				'files': [],
			}

			for k in ('artist', 'name', 'pubDate', 'owner'):
				album[k] = self.aton(em.getAttribute(k))

			have_front = False
			for em2 in em.getElementsByTagName('image'):
				album['images'].append({
					'medium': self.aton(em2.getAttribute('medium'), base_url),
					'original': self.aton(em2.getAttribute('original'), base_url),
					'type': self.aton(em2.getAttribute('type')),
				})
				if album['images'][-1]['type'] == 'front':
					have_front = True
			if not have_front and album['images']:
				album['images'][0]['type'] = 'front'

			for em2 in em.getElementsByTagName('track'):
				album['tracks'].append({
					'title': self.aton(em2.getAttribute('title')),
					'artist': self.aton(em2.getAttribute('artist')),
					'number': self.iton(em2.getAttribute('number')),
					'mp3-link': self.aton(em2.getAttribute('mp3-link'), base_url),
					'ogg-link': self.aton(em2.getAttribute('ogg-link'), base_url),
					'duration': self.aton(em2.getAttribute('duration')),
				})

			for em2 in em.getElementsByTagName('file'):
				album['files'].append({
					'name': self.aton(em2.getAttribute('name')),
					'uri': self.aton(em2.getAttribute('uri'), base_url),
					'type': self.aton(em2.getAttribute('type')),
					'size': self.iton(em2.getAttribute('size')),
				})

			if album['owner'] is None or album['owner'] == 'test@example.com':
				album['owner'] = 'justin.forest@gmail.com'

			return album
		return None

	def aton(self, value, prefix=None):
		if not value:
			return None
		if prefix is not None:
			value = prefix + value
		return value

	def iton(self, value):
		if not value:
			return None
		return int(value)

class Update(BaseRequestHandler):
	def get(self):
		self.force_admin()
		if self.request.get('kind') == 'artist':
			cls = model.SiteArtist
		elif self.request.get('kind') == 'album':
			cls = model.SiteAlbum
		else:
			return
		for obj in cls.all().fetch(1000):
			obj.put()
