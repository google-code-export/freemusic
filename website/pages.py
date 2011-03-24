# vim: set fileencoding=utf-8:

# Python imports.
import logging
import os
import urllib
import wsgiref.handlers

# GAE imports.
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template # required by django.template

from django.template import Context, Template


EDIT_TEMPLATE = u'''<html>
<head>
<title>Edit Page</title>
<style type="text/css">
body { margin: 1em; padding: 0; font: normal 10pt/14pt Ubuntu, sans-serif }
label span { display: block; margin-bottom: .25em }
div { margin-bottom: 1em }
input[type=text], textarea { padding: 2px 4px }
input[type=text] { width: 400px }
textarea { width: 100%; height: 200px; white-space: nowrap; overflow: auto }
</style>
</head>
<body>
<h1>Edit page "<a href="{{ page_path|escape }}">{{ page.name }}</a>"</h1>
<form method="post">
<input type="hidden" name="key" value="{% if page.is_saved %}{{ page.key }}{% endif %}"/>
<div><label><span>Name:</span> <input type="text" name="name" value="{% if page.name %}{{ page.name }}{% endif %}"/></label></div>
<div><label><span>Artist Name:</span> <input type="text" name="artist_name" value="{% if page.artist_name %}{{ page.artist_name }}{% endif %}"/></label></div>
<div><label><span>Domain Name:</span> <input type="text" name="domain_name" value="{% if page.domain_name %}{{ page.domain_name }}{% endif %}"/></label></div>
<div><label><span>Properties:</span> <textarea name="data">{% if page.data %}{{ page.data }}{% endif %}</textarea></label></div>
<div><label><span>Template:</span> <textarea name="template">{% if page.template %}{{ page.template }}{% endif %}</textarea></label></div>
<div><label><span>CSS:</span> <textarea name="css">{% if page.css %}{{ page.css }}{% endif %}</textarea></label></div>
<div><label><span>JavaScript:</span> <textarea name="js">{% if page.js %}{{ page.js }}{% endif %}</textarea></label></div>
<div><input type="submit" value="Save"/></div>
</form>
</body>
</html>'''

DEFAULT_TEMPLATE = u'''<html>
<head>
<title>Hello, world</title>
</head>
<body>
<h1>It Worked!</h1>
</body>
</html>'''


class WebPage(db.Model):
    name = db.StringProperty()
    artist_name = db.StringProperty()
    domain_name = db.StringProperty()
    theme = db.StringProperty()

    data = db.TextProperty()
    template = db.TextProperty()
    css = db.TextProperty()
    js = db.TextProperty()


class PageHandler(webapp.RequestHandler):
    def get(self, page_name):
        page_name = urllib.unquote(page_name).decode('utf-8')

        if 'edit' in self.request.arguments():
            return self.get_edit(page_name)

        page = WebPage.gql('WHERE name = :1', page_name).get()
        if page is None:
            return self.reply('Page not found.', 404)
        self.render(page.template or DEFAULT_TEMPLATE, page)

    def get_edit(self, page_name):
        page = WebPage.gql('WHERE name = :1', page_name).get() or WebPage(name=page_name, template=DEFAULT_TEMPLATE)
        self.render(EDIT_TEMPLATE, page)

    def post(self, page_name):
        page_name = urllib.unquote(page_name).decode('utf-8')
        if self.request.get('key'):
            page = db.get(db.Key(self.request.get('key')))
        else:
            page = WebPage()
        for key in page.fields().keys():
            setattr(page, key, self.request.get(key))
        page.put()
        self.redirect(self.request.uri)

    def reply(self, content, status=200, content_type='text/html'):
        self.response.set_status(status)
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(content)

    def render(self, template, page):
        variables = {
            'page_uri': self.request.uri,
            'page_path': self.request.path,
            'page': page,
        }

        t = Template(template).render(Context(variables))
        return self.reply(t)

if __name__ == '__main__':
    debug = os.environ['SERVER_SOFTWARE'].startswith('Development/')
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    # webapp.template.register_template_library('filters')
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        ('/pages/([^/]+)$', PageHandler),
    ], debug=debug))
