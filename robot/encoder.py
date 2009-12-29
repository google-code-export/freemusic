#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import logging, os, subprocess, tempfile
import tags

class Encoder:
	def __init__(self, forweb=False, albumart=None, tmpdir=None):
		self.forweb = forweb
		self.albumart = albumart
		self.tmpdir = tempfile.mkdtemp(prefix='encoder-', dir=tmpdir)

	def pipe(self, commands):
		logging.info('! ' + ' |\n  '.join([' '.join(command) for command in commands]))
		clist = [] # на всякий случай, чтобы деструкторов не было
		stdin = None
		for command in commands:
			clist.append(subprocess.Popen(command, stdout=subprocess.PIPE, stdin=stdin))
			stdin = clist[-1].stdout
		response = clist[-1].communicate()
		if clist[-1].returncode:
			raise Exception(response[1])
		return response[0]

	def file(self, filename, _tags):
		outname = self.encode_file(filename, os.path.join(self.tmpdir, '.'.join(os.path.basename(filename).split('.')[0:-1])))
		if _tags:
			tags.set(outname, _tags, self.albumart)
		return outname

	def replaygain(self, files):
		logging.info("No ReplayGain support for this file type.")
		return files

class MP3(Encoder):
	def encode_file(self, src, dst):
		dst += '.mp3'
		options = ['lame', '--quiet', '--replaygain-accurate']
		if self.forweb:
			options.append('--resample')
			options.append('44.1')
			options.append('-B')
			options.append('128')
		else:
			options.append('-v')
			options.append('-V')
			options.append('0')
			options.append('-h')
		options.append(src)
		options.append(dst)
		self.pipe([ options ])
		return dst

	def replaygain(self, files):
		self.pipe([ ['mp3gain', '-q'] + files ])
		return files

class OGG(Encoder):
	def encode_file(self, src, dst):
		dst += '.ogg'
		options = ['oggenc', '--quiet', '-o', dst]
		if self.forweb:
			options.append('--resample')
			options.append('44100')
		else:
			options.append('-q')
			options.append('6')
		options.append(src)
		self.pipe([ options ])
		return dst

	def replaygain(self, files):
		self.pipe([ ['vorbisgain', '-aq'] + files ])
		return files

class FLAC(Encoder):
	def encode_file(self, src, dst):
		dst += '.flac'
		options = ['flac', '-s', '--replay-gain', '-8', '-o', dst]
		if self.albumart:
			options.append('--picture=3|image/jpg|Cover|300x300x24|' + self.albumart)
		options.append(src)
		self.pipe([ options ])
		return dst

	def replaygain(self, files):
		return files # подсчитывается при кодировании

class Decoder(Encoder):
	def decode(self, filename):
		ext = filename.split('.')[-1].lower()
		result = {
			'wav': os.path.join(self.tmpdir, '.'.join(filename.split('.')[0:-1])) + '.wav',
			'lossless': False,
			'tags': tags.get(filename),
		}
		
		if ext == 'flac':
			self.pipe([[ 'flac', '-sd', '-o', result['wav'], filename ]])
			result['lossless'] = True
			result['target'] = 'flac'
		elif ext == 'mp3':
			self.pipe([[ 'lame', '--decode', '--quiet', filename, result['wav'] ]])
			result['target'] = 'mp3_dl'
		else:
			return None
		logging.debug("tags from %s: %s" % (filename, result['tags']))
		return result
