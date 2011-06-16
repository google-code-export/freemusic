# encoding=utf-8

import logging
import os
import sys
import urllib
import wsgiref

from google.appengine.dist import use_library
use_library('django', '0.96')

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


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


class Model(db.Model):
    def update(self, data):
        for k, v in data.items():
            if v:
                setattr(self, k, v)

    @classmethod
    def get_by_key(cls, key):
        obj = db.get(db.Key(key))
        return obj


class GAEDirCategory(Model):
    name = db.StringProperty()
    parents = db.StringListProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty()
    item_count = db.IntegerProperty()
    depth = db.IntegerProperty()

    def put(self):
        parents = add_parents([self.name])
        self.depth = len(parents)

        parents.remove(self.name)
        self.parents = parents

        return db.Model.put(self)

    def get_children(self):
        children = self.gql('WHERE parents = :1', self.name).fetch(100)
        return children

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

    @classmethod
    def get_by_name(cls, name):
        cat = cls.gql('WHERE name = :1', name).get()
        return cat

    @classmethod
    def get_toc(cls):
        toc = []
        categories = cls.gql('WHERE depth < 3').fetch(1000)

        for cat in categories:
            if cat.depth == 1:
                sub_categories = []
                for sub in categories:
                    if cat.name in sub.parents:
                        sub_categories.append(sub)
                toc.append({
                    'name': cat.name,
                    'children': sorted(sub_categories, key=lambda c: c.name.lower())[:3],
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
        return db.Model.put(self)

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

        logging.debug(self.data)

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
        (prefix + '/v/(.*)', ShowItemController),
        (prefix + '/(.*)', ShowCategoryController),
    ], debug=debug))


if __name__ == '__main__':
    serve('/c')
