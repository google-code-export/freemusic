"""Free Music Hub."""

import logging
import os

from google.appengine.ext.webapp import template


class Base(object):
    def __init__(self, rh):
        self.response = rh.response

    def render(self, template_name, data=None, content_type='application/xhtml+xml', ret=False):
        data = data or {}

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 'templates', template_name)
        logging.debug('Rendering %s' % path)

        result = template.render(path, data)

        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(result)
