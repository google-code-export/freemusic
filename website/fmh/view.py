"""Free Music Hub."""

import logging
import os

from google.appengine.ext.webapp import template


class Base(object):
    def __init__(self, rh=None):
        self.response = rh and rh.response

    def render(self, template_name, data=None, content_type='application/xhtml+xml', ret=False):
        if self.response is None:
            raise Exception('Bad view: response not set.')
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(self.render_template(template_name, data))

    def render_template(self, template_name, data=None):
        data = data or {}

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 'templates', template_name)
        logging.debug('Rendering %s' % path)

        return template.render(path, data)
