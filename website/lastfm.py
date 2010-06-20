# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Функции для взаимодействия с Last.fm.
"""

import config
import util

def get_events(artist_name):
	"""
	Возвращает XML дерево с предстоящими событиями для указанного исполнителя.
	http://www.lastfm.ru/api/show?service=117
	"""
	return util.fetchxml('http://ws.audioscrobbler.com/2.0/', {
		'method': 'artist.getevents',
		'artist': artist_name.encode('utf-8'),
		'api_key': config.LASTFM_KEY,
	})

def get_artist(artist_name):
	return util.fetchxml('http://ws.audioscrobbler.com/2.0/', {
		'method': 'artist.getInfo',
		'artist': artist_name.encode('utf-8'),
		'api_key': config.LASTFM_KEY,
	})
