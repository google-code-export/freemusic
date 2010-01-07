#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import datetime, logging, mimetypes, os, shutil, subprocess, tempfile, zipfile
import Image
from xml.sax.saxutils import quoteattr as escape
import albumart, encoder, myxml, tags

class File:
	def __init__(self, name):
		self.name = name # исходное имя файла
		self.type = mimetypes.guess_type(name)
		self.wav = None
		self.flac = None
		self.mp3_online = None
		self.mp3_dl = None
		self.ogg_online = None
		self.ogg_dl = None
		self.tags = {}
		self.lossless = False
		self.duration = None
		self.width = None
		self.height = None
		self.img_small = None
		self.img_medium = None

		try:
			img = Image.open(self.name)
			self.width, self.height = img.size
		except: pass

	def __str__(self):
		return self.name

	def __unicode__(self):
		return unicode(self.name)

	def tag(self, name):
		if name in self.tags:
			return list(self.tags[name])[0]
		return ''

	def process_audio(self, tmpdir, cover):
		raw = encoder.Decoder(tmpdir=tmpdir).decode(self.name)
		if raw:
			if 'target' in raw:
				setattr(self, raw['target'], self.name)
			self.wav = raw['wav']
			self.tags = raw['tags']
			try:
				self.duration = str(datetime.timedelta(0, int(tags.duration(self.name))))
			except Exception, e:
				logging.info("No duration for " + self.name + ": " + str(e))
			self.lossless = raw['lossless']
			if self.lossless:
				self.mp3_dl = encoder.MP3(forweb=False, tmpdir=tmpdir, albumart=cover).file(self.wav, self.tags)
				self.ogg_dl = encoder.OGG(forweb=False, tmpdir=tmpdir, albumart=cover).file(self.wav, self.tags)
				self.flac = encoder.FLAC(tmpdir=tmpdir, albumart=cover).file(self.wav, self.tags)
			self.mp3_online = encoder.MP3(forweb=True, tmpdir=tmpdir, albumart=cover).file(self.wav, self.tags)
			self.ogg_online = encoder.OGG(forweb=True, tmpdir=tmpdir, albumart=cover).file(self.wav, self.tags)

		if self.is_image():
			self.img_small = albumart.resize(self.name, 100)
			self.img_medium = albumart.resize(self.name, 200)

	def is_audio(self):
		if self.wav:
			return True
		return False

	def is_image(self):
		if self.width:
			return True
		return False

	def uploadable(self):
		lst = []
		for k in ['mp3_online', 'ogg_online', 'img_small', 'img_medium']:
			if getattr(self, k):
				lst.append(getattr(self, k))
		if not len(lst) or self.is_image():
			lst.append(self.name)
		return lst

	def get_track_xml(self):
		if self.is_audio():
			try:
				tracknumber = int(self.tag('tracknumber').split('/')[0])
			except:
				tracknumber = None
			return myxml.em(u'track', {
				'artist': self.tag('artist'),
				'title': self.tag('title'),
				'number': tracknumber,
				'duration': self.duration,
				'mp3-link': myxml.uri(os.path.basename(self.mp3_online)),
				'ogg-link': myxml.uri(os.path.basename(self.ogg_online)),
			})
		return u''

	def get_file_xml(self):
		if not self.is_audio() and not self.is_image():
			name = os.path.basename(self.name)
			size = os.path.getsize(self.name)
			return myxml.em('file', {
				'name': name,
				'uri': myxml.uri(name),
				'type': self.type[0],
				'size': os.path.getsize(self.name),
			})
		return u''

	def get_image_xml(self):
		if self.is_image():
			return myxml.em(u'image', {
				'original': myxml.uri(os.path.basename(self.name)),
				'small': myxml.uri(os.path.basename(self.img_small)),
				'medium': myxml.uri(os.path.basename(self.img_medium)),
				})
		return u''

class Transcoder:
	"""
	Основной обработчик транскодирования. Получает имя исходного ZIP файла,
	распаковывает его, формирует MP3/OGG файлы для онлайн-прослушивания
	и архивы для скачивания.
	"""
	def __init__(self, upload_dir, owner):
		self.ready = None
		self.zipname = None # исходный файл, для формирования имени выходных архивов
		self.realname = None # исходное имя файла прискачивании
		self.tmpdir = tempfile.mkdtemp(prefix='freemusic-')
		self.upload_dir = upload_dir
		self.albumart = None
		self.files = []
		self.logname = None
		self.owner = owner

		self.logname = os.path.join(self.tmpdir, 'transcoding-log.txt')
		logging.basicConfig(filename=self.logname, level=logging.DEBUG)
		print "Logging to " + self.logname

	def __del__(self):
		logging.basicConfig(filename=None)
		if self.tmpdir:
			if not self.upload_dir:
				print "No upload_dir, examining."
				self.examine(self.tmpdir)
			print "Removing " + self.tmpdir
			return shutil.rmtree(self.tmpdir)

	def transcode(self, zipname, realname):
		"""
		Обрабатывает указанный архив, возвращает имена сгенерированных файлов.
		"""
		self.zipname = zipname
		self.realname = realname
		self.files = [File(f) for f in self.unzip(zipname)]
		self.albumart = albumart.find(self.files, os.path.join(self.tmpdir, '__folder.jpg'))

		self.process_audio()
		self.makeDownloadableFiles()
		self.makeXML()
		return self.upload()

	def upload(self):
		if self.upload_dir:
			files = []
			if self.logname and os.path.exists(self.logname):
				files.append(self.logname)
			for f in self.files:
				for ff in f.uploadable():
					files.append(ff)
			if len(files):
				dir = tempfile.mkdtemp(prefix='', dir=self.upload_dir)
				os.chmod(dir, 0755)
				for file in files:
					shutil.move(file, dir)
			return os.path.join(os.path.basename(dir), 'album.xml')

	def process_audio(self):
		for f in self.files:
			f.process_audio(self.tmpdir, self.albumart)

		self.replaygain(encoder.MP3, 'mp3_online')
		self.replaygain(encoder.MP3, 'mp3_dl')
		self.replaygain(encoder.OGG, 'ogg_online')
		self.replaygain(encoder.OGG, 'ogg_dl')

	def replaygain(self, encoder, attr):
		files = [getattr(file, attr) for file in self.files if hasattr(file, attr) and getattr(file, attr)]
		if len(files):
			encoder(tmpdir=self.tmpdir).replaygain(files)

	def unzip(self, zipname):
		"""
		Распаковывает указанный ZIP архив во временную папку,
		возвращает список с именами файлов.
		"""
		logging.info("unzipping " + zipname)
		result = []
		zip = zipfile.ZipFile(zipname)
		for f in sorted(zip.namelist()):
			if not f.endswith('/'):
				result.append(os.path.join(self.tmpdir, os.path.basename(f)))
				out = open(result[-1], 'wb')
				out.write(zip.read(f))
				out.close()
				logging.info("  found " + f)
		return result

	def makeDownloadableFiles(self):
		prefix = os.path.join(self.tmpdir, os.path.splitext(self.realname)[0])
		self.mkzip(prefix + '-ogg.zip', 'ogg_dl')
		self.mkzip(prefix + '-mp3.zip', 'mp3_dl')
		self.mkzip(prefix + '-flac.zip', 'flac')

	def mkzip(self, zipname, attr):
		if 'flac' == attr:
			files = [getattr(file, attr) for file in self.files if getattr(file, attr) and file.lossless]
		else:
			files = [getattr(file, attr) for file in self.files if getattr(file, attr)]
		if not len(files):
			return
		logging.info("creating " + zipname)
		files += [file.name for file in self.files if not file.is_audio()]

		zip = zipfile.ZipFile(zipname, 'a')
		for file in files:
			if not file.endswith('.zip'):
				logging.info("  adding " + file)
				zip.write(file, os.path.basename(file))
		zip.close()
		self.files.append(File(zipname))

	def makeXML(self):
		artist, album = self.find_meta()
		contents = u'' # u'<?xml version="1.0"?>\n<album name=%s artist=%s>' % (escape(album), escape(artist))
		for w, m in [(u'tracks', File.get_track_xml), (u'images', File.get_image_xml), (u'files', File.get_file_xml)]:
			contents += myxml.em(w, content=u''.join([m(file) for file in self.files]), empty=False)

		xml = u'<?xml version="1.0"?>\n'
		xml += myxml.em(u'album', {
			'artist': artist,
			'name': album,
			'owner': self.owner,
		}, contents)

		filename = os.path.join(self.tmpdir, 'album.xml')
		open(filename, 'w').write(xml.encode('utf-8'))
		self.files.append(File(filename))

	def find_meta(self):
		artists = []
		album = None

		for file in self.files:
			if file.is_audio() and file.tags:
				if 'artist' in file.tags and file.tags['artist'][0] not in artists:
					artists.append(file.tags['artist'][0])
				if 'album' in file.tags:
					album = file.tags['album'][0]

		if len(artists) != 1:
			artists = ['Various Artists']
		if not album:
			album = os.path.splitext(os.path.basename(self.zipname))[0]

		return (artists[0], album)

	def examine(self, path):
		print 'Examine folder contents, then ^D'
		old = os.getcwd()
		os.chdir(path)
		p = subprocess.Popen(['bash', '-i'])
		p.communicate()
		os.chdir(old)
