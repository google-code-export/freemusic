# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Функции для взаимодействия с Last.fm.
"""

import util

LASTFM_KEY = 'e1cedb5b6c9aa0c38a69f752c6f510d2' # http://www.lastfm.ru/api/account

def get_events(artist_name):
	"""
	Возвращает XML дерево с предстоящими событиями для указанного исполнителя.
	http://www.lastfm.ru/api/show?service=117
	"""
	return util.fetchxml('http://ws.audioscrobbler.com/2.0/', {
		'method': 'artist.getevents',
		'artist': artist_name.encode('utf-8'),
		'api_key': LASTFM_KEY,
	})
