"""Free Music Hub.

The web server part."""

import logging
import os
import urllib
import urlparse
import wsgiref.handlers

from google.appengine.ext import webapp

from fmh import albums
from fmh import files
from fmh import model


class DataHandler(albums.RequestHandler):
    def get(self):
        output = u"artists:\n"

        for artist in sorted(model.Artist.all().fetch(1000), key=lambda a: a.name.lower()):
            output += u"- name: %s\n" % self.escape(artist.name)
            output += self.get_artist_links(artist)

            albums = sorted(model.Album.find_by_artist(artist.name), key=lambda a: a.title.lower())
            if albums:
                output += u"  releases:\n"
                for album in albums:
                    output += u"  - name: %s\n" % self.escape(album.title)
                    if album.date_released:
                        output += u"    date: %s\n" % album.date_released
                    if album.labels:
                        output += u"    labels: [%s]\n" % u", ".join(sorted(album.labels))
                    if album.homepage:
                        output += u"    links:\n"
                        output += u"    - %s\n" % album.homepage
                    output += self.get_album_files(album)

        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        self.response.out.write(output.encode("utf-8"))

    def escape(self, text):
        if ": " in text or "[" in text or text.isdigit():
            return u"\"%s\"" % text
        return text

    def get_artist_links(self, artist):
        links = []
        if artist.homepage:
            links.append(artist.homepage)
        if artist.lastfm_name:
            links.append("http://www.last.fm/music/%s" % urllib.quote(artist.lastfm_name.encode("utf-8")))
        if not links:
            return ""
        output = u"  links:\n"
        for link in links:
            output += u"  - %s\n" % link
        return output

    def get_album_files(self, album):
        album = album.get_old()
        if not album:
            return ""

        files = album.find_files(content_type="application/")
        if not files:
            return ""

        hostname = urlparse.urlparse(self.request.url).netloc

        output = u"    files:\n"
        for file in files:
            output += u"    - http://%s/download/%u/%s\n" % (hostname, file.id, file.filename)
        return output


handlers = [
    ('/', albums.BestController),
    ('/album/(\d+)', albums.ViewController),
    ('/album/(\d+)/cover\.jpg', albums.CoverController),
    ('/album/(\d+)/download', albums.DownloadController),
    ('/album/(\d+)/edit', albums.EditController),
    ('/album/(\d+)/json', albums.JSONController),
    ('/album/(\d+)/review', albums.ReviewController),
    ('/album/add$', albums.AddController),
    ('/album/search', albums.SearchController),
    ('/album/search/best', albums.BestController),
    ('/album/search/new', albums.NewController),
    ('/album/upgrade', albums.UpgradeController),
    ('/data\.yaml', DataHandler),
    ('/file/([^/]+)/.*', files.DownloadController),
]

def run():
    debug = os.environ['SERVER_SOFTWARE'].startswith('Development/')
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication(handlers, debug=debug))


if __name__ == '__main__':
    run()
