# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from logging import debug as log
import datetime

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db

import base
import mail
import model
import myxml
import rss

class SiteDownload(db.Model):
	user = db.UserProperty(required=True)
	file = db.LinkProperty(required=True)
	album = db.ReferenceProperty(model.SiteAlbum)
	published = db.DateTimeProperty(auto_now_add=True)

class Viewer(base.BaseRequestHandler):
	def get(self, id):
		album = self.get_album(id)

		self.send_html('album.html', {
			'album': album,
			'tracks': model.SiteTrack.gql('WHERE album = :1 ORDER BY number', album).fetch(100),
			'images': model.SiteImage.gql('WHERE album = :1', album).fetch(100),
		})

	def get_events(self, album):
		xml = u''
		events = [e.xml for e in model.Event.gql('WHERE artist = :1', album.artist).fetch(1000)]
		if len(events):
			xml = myxml.em(u'events', content=u''.join(events))
		return xml

	def get_album(self, id):
		if id:
			album = model.SiteAlbum.gql('WHERE id = :1', int(id)).get()
			if album:
				return album
		raise base.HTTPException(404, u'Нет такого альбома.')

class Playlist(Viewer):
	def get(self, id, format):
		album = self.get_album(id)
		tracks = model.SiteTrack.gql('WHERE album = :1 ORDER BY number', album).fetch(1000)
		output = u'[playlist]\nNumberOfEntries=%u\n' % len(tracks)
		index = 1
		for track in tracks:
			if format == 'mp3':
				url = track.mp3_link
			else:
				url = track.ogg_link
			output += u'File%u=%s\nTitle%u=%s\n' % (index, url, index, track.title)
			index += 1
		self.sendAny('text/plain', output) # audio/x-scpls

class FileViewer(Viewer):
	xsltName = 'album-files.xsl'

	def get(self, album_id):
		self.sendXML(self.get_album(int(album_id)).xml)

class Editor(Viewer):
	xsltName = 'albums.xsl'

	def get(self, id):
		self.check_access()
		self.sendXML('<form>' + self.get_album(id).xml + '</form>')

	def post(self, id):
		try:
			album = self.get_album(id)
			self.force_user_or_admin(album.owner)

			album.name = self.request.get(u'name')
			album.release_date = datetime.datetime.strptime(self.request.get(u'pubDate'), '%Y-%m-%d').date()
			album.text = self.request.get(u'text')
			album.labels = [unicode(label.strip()).lower() for label in self.request.get('labels').split(',')]

			# Переименовываем дорожки
			self.rename_tracks(album)

			album.put()
			album.artist.put() # обновление XML

			self.redirect('/album/' + str(album.id))
		except Exception, e:
			log([(arg, self.request.get(arg)) for arg in self.request.arguments()])
			raise

	def rename_tracks(self, album):
		"Извлекает из запроса номера и имена дорожек, сохраняет их."
		data = {}
		for arg in self.request.arguments():
			if arg.startswith('track.') and self.request.get(arg):
				data[int(arg.split('.', 1)[1])] = self.request.get(arg)
		if data:
			for track in model.SiteTrack.gql('WHERE album = :1', album).fetch(1000):
				if track.id in data:
					track.title = data[track.id]
					track.put()


class Delete(Viewer):
	xsltName = 'albums.xsl'

	def get(self, id):
		album = self.get_album(id)
		self.sendXML(myxml.em(u'delete-album', {
			'id': album.id,
			'name': album.name,
			'artist-id': album.artist.id,
			'artist-name': album.artist.name,
		}))

	def post(self, id):
		album = self.get_album(id)
		for cls in (model.SiteImage, model.SiteTrack, model.SiteFile, model.SiteAlbumReview):
			items = cls.gql('WHERE album = :1', album).fetch(1000)
			if items:
				for item in items:
					item.delete()

		artist = album.artist
		album.delete()

		artist.put() # обновление XML
		self.redirect('/artist/' + str(artist.id))

	def get_album(self, id):
		album = Viewer.get_album(self, id)
		user = self.force_user()
		if album.owner != user and not self.is_admin():
			raise base.ForbiddenException
		return album

class RSSHandler(rss.RSSHandler):
	def get(self):
		items = [{
			'title': album.name,
			'link': 'album/' + str(album.id),
		} for album in model.SiteAlbum.all().order('-release_date').fetch(20)]
		self.sendRSS(items, title=u'Новые альбомы')

class Stars(base.BaseRequestHandler):
	def get(self):
		if self.request.get('id'):
			album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
			a = model.SiteAlbumStar.gql('WHERE user = :1 AND album = :2', self.force_user(), album).get()
			if a is not None:
				return self.sendJSON({
					'star': 1,
				})
		self.sendJSON({
			'star': 0,
		})

	def post(self):
		user = users.get_current_user()
		memcache.delete('/player?user=' + user.nickname())
		memcache.delete('/u/' + user.nickname())
		album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
		if album is not None:
			user = self.force_user()
			star = model.SiteAlbumStar.gql('WHERE user = :1 AND album = :2', user, album).get()

			status = self.request.get('status') == 'true'
			if status and not star:
				model.SiteAlbumStar(user=user, album=album).put()
			elif not status and star:
				star.delete()

			if status:
				return self.sendJSON({
					'notify': 'Альбом добавлен в <a href="/player?user=%s">коллекцию</a>.&nbsp; <a href="http://code.google.com/p/freemusic/wiki/Collection" target="_blank">Подробнее</a>' % users.get_current_user().nickname(),
				})
		self.sendJSON({'notify':''})

class Review(base.BaseRequestHandler):
	def get(self):
		"""
		Вывод рецензий.
		"""
		if self.request.get('album'):
			album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('album'))).get()
			xml = u''.join([one.xml for one in model.SiteAlbumReview.gql('WHERE album = :1', album)])
			self.sendXML(myxml.em(u'reviews', None, xml))

	def post(self):
		"""
		Добавление новой рецензии. Обрабатываются поля формы: id, comment, sound,
		arrangement, vocals, lyrics, prof.
		
		Возвращается JSON объект со свойствами status и message. В случае ошибки
		message будет содержать сообщение.
		"""
		user = self.get_current_user()
		album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
		response = { 'status': 'ok', 'message': '' }

		review = model.SiteAlbumReview.gql('WHERE album = :1 AND author = :2', album, user).get()
		if review is not None:
			response['status'] = 'duplicate'
			response['message'] = 'Вы уже писали рецензию на этот альбом.'
		else:
			status = 'ok'
			review = model.SiteAlbumReview(user=user, album=model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get())
			for k in ('sound', 'arrangement', 'vocals', 'lyrics', 'prof'):
				rate = self.request.get(k)
				if rate and int(rate) <= 5:
					setattr(review, 'rate_' + k, int(rate))
			review.comment = self.request.get('comment')
			review.put()
			album.put() # сохраняем альбом для обновления средней оценки

			memcache.delete('/u/' + user.nickname())

		self.sendJSON(response)

class AlbumLabels(base.BaseRequestHandler):
	"""
	Управление метками альбома.
	"""
	def get(self):
		"""
		Получение списка меток. Если есть пользовательские метки,
		возвращаются они, в противном случае — общие метки альбома.
		"""
		album = self.get_album()
		labels = sorted(self.get_labels(album))
		text = u', '.join(labels)
		self.sendJSON({
			'id': album.id,
			'list': labels,
			'text': text,
			'form': u'<form method="post" action="/album/labels?id=%u"><textarea name="labels">%s</textarea><button>Сохранить</button></form>' % (album.id, text),
		})

	def get_labels(self, album):
		user = users.get_current_user()
		if user is None:
			return album.labels
		return [l.label for l in model.SiteAlbumLabel.gql('WHERE album = :1 AND user = :2', album, user).fetch(1000)]

	def post(self):
		user = self.force_user()
		album = self.get_album()
		for l in model.SiteAlbumLabel.gql('WHERE album = :1 AND user = :2', album, user).fetch(1000):
			l.delete()
		for kw in self.request.get('labels').split(','):
			model.SiteAlbumLabel(user=user, album=album, label=kw.strip().lower()).put()

		self.sendJSON({
			'html': u'<p>Метки: ' + u', '.join([u'<a href="/?label=%s">%s</a>' % (l, l) for l in sorted(self.get_labels(album))]) + u'.',
			'notification': u'Ваши метки будут применены через какое-то время.',
		})

		memcache.delete('/u/' + user.nickname())
		taskqueue.Task(url='/album/labels/update', params={'id': album.id}).add()

	def get_album(self, id=None):
		if id is None:
			id = int(self.request.get('id'))
		album = model.SiteAlbum.gql('WHERE id = :1', id).get()
		if album is None:
			raise HTTPException(404, u'Нет такого альбома.')
		return album

class AlbumLabelUpdater(base.BaseRequestHandler):
	def post(self):
		if 'X-AppEngine-QueueName' in self.request.headers:
			album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
			if album is not None:
				labels = []
				for l in model.SiteAlbumLabel.gql('WHERE album = :1', album).fetch(1000):
					l = l.label.lower()
					if l not in labels:
						labels.append(l)
				album.labels = labels
				album.put()

				taskqueue.Task(url='/labels/cache').add()

class DownloadTracker(base.BaseRequestHandler):
	def get(self):
		user = users.get_current_user()
		if user is not None:
			album = model.SiteAlbum.gql('WHERE id = :1', int(self.request.get('album'))).get()
			if album is not None:
				dl = SiteDownload(user=user, album=album, file=self.request.get('file'))
				dl.put()

class ReviewBegger(base.BaseRequestHandler):
	"""
	Отправляет пользователям, скачивавшим альбомы, просьбы написать
	рецензию. Запускается по крону.
	"""
	def get(self):
		for dl in SiteDownload.all().order('-published').fetch(10):
			mail.send2(dl.user.email(), 'ask-for-a-review', {
				'dl': dl,
				'host': self.request.host,
				'base': self.getBaseURL(),
			})
			dl.delete()

if __name__ == '__main__':
	base.run([
		('/album/(\d+)$', Viewer),
		('/album/(\d+)\.(mp3|ogg)\.pls$', Playlist),
		('/album/(\d+)/delete$', Delete),
		('/album/(\d+)/edit$', Editor),
		('/album/(\d+)/files$', FileViewer),
		('/album/download', DownloadTracker),
		('/album/labels', AlbumLabels),
		('/album/labels/update', AlbumLabelUpdater),
		('/album/review', Review),
		('/album/review/beg', ReviewBegger),
		('/albums\.rss', RSSHandler),
	])
