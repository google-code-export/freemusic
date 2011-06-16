# encoding=utf-8

import HTMLParser
import logging
import os
import re
import sys
import urllib
import wsgiref

from google.appengine.dist import use_library
use_library('django', '0.96')

from django.utils import simplejson
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

LAST_FM_KEY = '730a57dbf9b5b7f2be60f63754aa3162'


class NotFound(Exception): pass
class Forbidden(Exception): pass

def split(value, sep='\n'):
    return [ p.strip() for p in value.split(sep) if p.strip() ]

def url_unquote(value):
    value = urllib.unquote(value).replace('_', ' ')
    return value.decode('utf-8')

def add_parents(categories):
    """Returns a list of categories with their parents added."""
    names = []
    for cat in categories:
        parts = cat.split(u'/')
        while parts:
            name = u'/'.join(parts)
            if name not in names:
                names.append(name)
            del parts[-1]
    return sorted(names)


class HTMLStripper(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

    @classmethod
    def process(cls, html):
        s = cls()
        s.feed(html)
        text = s.get_data()

        lines = [u'<p>%s</p>' % l.strip() for l in text.split('\n') if l.strip()]
        text = u''.join(lines)

        return text


class Model(db.Model):
    def update(self, data):
        for k, v in data.items():
            if v or (v == False):
                setattr(self, k, v)

    @classmethod
    def get_by_key(cls, key):
        obj = db.get(db.Key(key))
        return obj


class GAEDirCategory(Model):
    name = db.StringProperty()
    parents = db.StringListProperty()
    first_parent = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty()
    item_count = db.IntegerProperty()
    depth = db.IntegerProperty()
    # Promotes the category to the front page.
    promote = db.BooleanProperty()

    def put(self):
        parents = add_parents([self.name])
        self.depth = len(parents)

        parents.remove(self.name)
        self.parents = parents
        self.first_parent = max(parents)

        return db.Model.put(self)

    def get_children(self):
        """Returns a sorted list of immediate children."""
        children = self.gql('WHERE first_parent = :1', self.name).fetch(100)

        # fallback to old method
        if not children:
            children = []
            for child in self.gql('WHERE parents = :1', self.name).fetch(100):
                if child.depth == self.depth + 1:
                    children.append(child)

        return sorted(children, key=lambda c: c.name.lower())

    def get_items(self):
        """Returns all items in this category."""
        return GAEDirEntry.gql('WHERE all_categories = :1', self.name).fetch(100)

    def get_path(self):
        result = []
        parts = self.name.split(u'/')
        while parts:
            result.insert(0, (parts[-1], u'/'.join(parts)))
            del parts[-1]
        return result

    def get_name(self):
        return self.name.split('/')[-1]

    def get_item_count(self):
        return self.item_count or 0

    def update_item_count(self):
        self.item_count = GAEDirEntry.gql('WHERE categories = :1', self.name).count()

    def __repr__(self):
        return u'<gaedir.Category name=%s promote=%s>' % (self.name, self.promote or False)

    @classmethod
    def get_by_name(cls, name):
        cat = cls.gql('WHERE name = :1', name).get()
        return cat

    @classmethod
    def get_toc(cls):
        """Returns a structure with the top categories, to show on the front
        page.  The structure is a list of (name, children)."""
        toc = []
        categories = cls.gql('WHERE depth < 3').fetch(1000)

        for cat in categories:
            if cat.depth == 1:
                promoted = []
                normal = []
                for sub in categories:
                    if cat.name in sub.parents:
                        if sub.promote:
                            promoted.append(sub)
                        else:
                            normal.append(sub)

                limit = max(3, len(promoted))
                children = list(promoted + normal)[:limit]

                if cat.name == 'Music':
                    logging.debug(promoted)
                    logging.debug(normal)

                toc.append({
                    'name': cat.name,
                    'children': sorted(children, key=lambda c: c.name.lower())[:3],
                })

        return sorted(toc, key=lambda x: x['name'].lower())


class GAEDirEntry(Model):
    name = db.StringProperty()
    categories = db.StringListProperty()
    links = db.StringListProperty()
    picture = db.LinkProperty()
    description = db.TextProperty()

    # Used by the cron job to update information from external sources.
    last_updated = db.DateTimeProperty(auto_now_add=True)

    # This includes implicitly added parent categories.
    all_categories = db.StringListProperty()

    def put(self):
        self.update_all_categories()
        # self.update_counts()
        db.Model.put(self)

    def schedule_update(self):
        taskqueue.add(url=os.environ['CAT_URL_PREFIX'] + '/update/entry', params={ 'key': str(self.key()) })

    def update_all_categories(self):
        """Fills self.all_categories with parent names, adds missing categories
        to the database."""
        self.all_categories = add_parents(self.categories)
        for cat_name in self.all_categories:
            if GAEDirCategory.get_by_name(cat_name) is None:
                GAEDirCategory(name=cat_name).put()

    def update_counts(self):
        names = []
        for cat in self.categories:
            parts = cat.split(u'/')
            while parts:
                name = u'/'.join(parts)
                if name not in names:
                    names.append(name)
                del parts[-1]

        for name in names:
            cat = GAEDirCategory.get_by_name(name)
            if cat is None:
                cat = GAEDirCategory(name=name, item_count=0)
            cat.item_count += 1
            cat.put()

    def get_categories(self):
        return sorted(self.categories, key=lambda n: n.lower())

    @classmethod
    def get_by_name(cls, name):
        return cls.gql('WHERE name = :1', name).get()


class Controller(webapp.RequestHandler):
    def redirect(self, path):
        path = os.environ.get('CAT_URL_PREFIX') + path
        path = urllib.quote(path.replace(' ', '_'))
        logging.debug('Redirecting to %s' % path)
        return webapp.RequestHandler.redirect(self, path)


class View:
    template_name = 'missing.html'
    content_type = 'text/html'

    def __init__(self, data=None):
        self.data = data or {}
        self.data['class_name'] = self.__class__.__name__
        self.data['path_prefix'] = os.environ['CAT_URL_PREFIX']
        self.data['user'] = users.get_current_user()
        self.data['is_admin'] = users.is_current_user_admin()
        if self.data['is_admin']:
            if os.environ['SERVER_SOFTWARE'].startswith('Development/'):
                self.data['admin_url'] = '/_ah/admin'
            else:
                self.data['admin_url'] = 'https://appengine.google.com/dashboard?app_id=' + os.environ['APPLICATION_ID']

    def reply(self, request):
        self.data['path'] = request.request.path
        self.data['base'] = os.environ.get('CAT_URL_PREFIX')
        if self.data['user']:
            self.data['log_out_url'] = users.create_logout_url(os.environ['PATH_INFO'])
        else:
            self.data['log_in_url'] = users.create_login_url(os.environ['PATH_INFO'])

        path = os.path.join(os.path.dirname(__file__), 'templates', self.template_name)
        content = template.render(path, self.data)

        request.response.headers['Content-Type'] = self.content_type + '; charset=utf-8'
        request.response.out.write(content)


class ShowCategoryController(webapp.RequestHandler):
    def get(self, path):
        cat = GAEDirCategory.get_by_name(url_unquote(path))
        if not cat:
            raise NotFound
        ShowCategoryView({
            'cat': cat,
            'children': sorted(cat.get_children(), key=lambda c: c.name.lower()),
            'items': sorted(cat.get_items(), key=lambda i: i.name.lower()),
        }).reply(self)

class ShowCategoryView(View):
    template_name = 'show_category.html'


class EditCategoryController(webapp.RequestHandler):
    """Category editor."""
    def get(self):
        cat = GAEDirCategory.get_by_key(self.request.get('key'))
        if not cat:
            raise NotFound
        if not users.is_current_user_admin():
            raise Forbidden
        EditCategoryView({
            'cat': cat,
        }).reply(self)

    def post(self):
        cat = GAEDirCategory.get_by_key(self.request.get('key'))
        if not cat:
            raise NotFound
        if not users.is_current_user_admin():
            raise Forbidden
        cat.update({
            'name': self.request.get('name'),
            'link': self.request.get('link'),
            'promote': bool(self.request.get('promote')),
        })
        cat.put()
        self.redirect(os.environ['CAT_URL_PREFIX'] + '/' + cat.name.encode('utf-8'))

class EditCategoryView(View):
    template_name = 'edit_category.html'


class SubmitEntryController(Controller):
    def get(self):  
        if not users.is_current_user_admin():
            raise Forbidden
        SubmitEntryView({
            'category_name': self.request.get('cat'),
        }).reply(self)

    def post(self):
        if not users.is_current_user_admin():
            raise Forbidden
        item = GAEDirEntry()
        item.update({
            'name': self.request.get('name'),
            'categories': split(self.request.get('categories'), '\n'),
            'links': split(self.request.get('links'), '\n'),
            'picture': self.request.get('picture'),
            'description': self.request.get('description'),
        })
        item.put()
        item.schedule_update()
        self.redirect('/v/' + item.name.encode('utf-8'))

class SubmitEntryView(View):
    template_name = 'submit_item.html'


class ShowItemController(Controller):
    def get(self, name):
        item = GAEDirEntry.get_by_name(url_unquote(name))
        if not item:
            raise NotFound
        ShowItemView({
            'item': item,
        }).reply(self)

class ShowItemView(View):
    template_name = 'show_item.html'

    def __init__(self, data):
        if data['item'].links:
            data['item_links'] = self.format_links(data['item'].links)
        View.__init__(self, data)

    def format_links(self, links):
        result = []
        for link in links:
            parts = link.split('/')
            host = parts[2]
            if host.startswith('www.'):
                host = host[4:]
            result.append({
                'name': host,
                'href': link,
            })
        return sorted(result, key=lambda l: l['name'].lower())


class EditEntryController(Controller):
    def get(self):
        item = GAEDirEntry.get_by_key(self.request.get('key'))
        if not item:
            raise NotFound
        if not users.is_current_user_admin():
            raise Forbidden
        EditEntryView({
            'item': item,
        }).reply(self)

    def post(self):
        item = GAEDirEntry.get_by_key(self.request.get('key'))
        if not item:
            raise NotFound
        if not users.is_current_user_admin():
            raise Forbidden
        item.update({
            'name': self.request.get('name'),
            'categories': split(self.request.get('categories'), '\n'),
            'links': split(self.request.get('links'), '\n'),
            'picture': self.request.get('picture'),
            'description': self.request.get('description'),
        })
        item.put()
        item.schedule_update()
        self.redirect('/v/' + item.name.encode('utf-8'))

class EditEntryView(View):
    template_name = 'edit_item.html'


class IndexController(webapp.RequestHandler):
    def get(self):
        IndexView({
            'toc': GAEDirCategory.get_toc(),
        }).reply(self)

class IndexView(View):
    template_name = 'index.html'


class UpdateEntryController(Controller):
    def post(self):
        entry = GAEDirEntry.get_by_key(self.request.get('key'))
        if not entry:
            raise NotFound
        """
        if not users.is_current_user_admin():
            raise Forbidden
        """

        update = self.update_from_lastfm(entry)
        if update:
            entry.put()

    def update_from_lastfm(self, entry):
        update = False
        for link in entry.links:
            match = re.match('http://(?:www.last.fm|www.lastfm.ru)/music/(.+)', link)
            if match:
                url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=%s&api_key=%s&format=json' % (match.group(1), LAST_FM_KEY)
                data = simplejson.loads(urlfetch.fetch(url=url).content)

                for image in data['artist']['image']:
                    if image['size'] == 'large':
                        entry.picture = image['#text']
                        logging.info(u'Found picture for %s: %s' % (entry.name, entry.picture))
                        update = True

                try:
                    entry.description = HTMLStripper.process(data['artist']['bio']['content'])
                    logging.debug(entry.description)
                except KeyError: pass
        return update


def serve(prefix=''):
    debug = True
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    os.environ['CAT_URL_PREFIX'] = prefix
    webapp.template.register_template_library('gaedir.filters')
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        (prefix + '/', IndexController),
        (prefix + '/submit', SubmitEntryController),
        (prefix + '/edit/entry', EditEntryController),
        (prefix + '/edit/category', EditCategoryController),
        (prefix + '/update/entry', UpdateEntryController),
        (prefix + '/v/(.*)', ShowItemController),
        (prefix + '/(.*)', ShowCategoryController),
    ], debug=debug))


if __name__ == '__main__':
    serve('/c')
