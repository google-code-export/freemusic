"""Free Music Hub.

The web server part."""

import logging
import os
import wsgiref.handlers

from google.appengine.ext import webapp

import fmh.albums as albums


handlers = [
    ('/album/(\d+)$', albums.ViewController),
    ('/album/add$', albums.AddController),
]

def run():
    debug = os.environ['SERVER_SOFTWARE'].startswith('Development/')
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication(handlers, debug=debug))


if __name__ == '__main__':
    run()