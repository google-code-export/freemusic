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

def split(value, sep=' '):
    return [ p.strip() for p in value.split(sep) ]


class Category(db.Model):
    name = db.StringProperty()
    parents = db.StringListProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty()
    item_count = db.IntegerProperty()
    depth = db.IntegerProperty()

    def put(self):
        if '/' in self.name:
            self.parents = [ u'/'.join(self.name.split('/')[:-1]) ]
        else:
            self.parents = ['/']
        return db.Model.put(self)

    def get_children(self):
        children = self.gql('WHERE parents = :1', self.name).fetch(100)
        return children

    def get_items(self):
        return CatItem.gql('WHERE categories = :1', self.name).fetch(100)

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
        self.item_count = CatItem.gql('WHERE categories = :1', self.name).count()

    @classmethod
    def get_by_name(cls, name):
        cat = cls.gql('WHERE name = :1', name).get()
        return cat

    @classmethod
    def get_toc(cls):
        return sorted(cls.all().fetch(100), key=lambda c: c.name.lower())


class CatItem(db.Model):
    name = db.StringProperty()
    categories = db.StringListProperty()
    links = db.StringListProperty()

    def put(self):
        if not self.is_saved():
            self.update_counts()
        return db.Model.put(self)

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
            cat = Category.get_by_name(name)
            if cat is None:
                cat = Category(name=name, item_count=0)
            cat.item_count += 1
            cat.put()

    @classmethod
    def get_by_name(cls, name):
        return cls.gql('WHERE name = :1', name).get()


class View:
    template_name = 'missing.html'
    content_type = 'text/html'

    def __init__(self, data=None):
        self.data = data or {}
        self.data['class_name'] = self.__class__.__name__
        self.data['path_prefix'] = os.environ['CAT_URL_PREFIX']

    def reply(self, request):
        self.data['path'] = request.request.path

        path = os.path.join(os.path.dirname(__file__), 'templates', self.template_name)
        content = template.render(path, self.data)

        logging.debug(self.data)

        request.response.headers['Content-Type'] = self.content_type + '; charset=utf-8'
        request.response.out.write(content)


class BrowserController(webapp.RequestHandler):
    def get(self, path):
        cat = Category.get_by_name(urllib.unquote(path).replace('_', ' '))
        if not cat:
            raise NotFound
        BrowserView({
            'cat': cat,
            'children': sorted(cat.get_children(), key=lambda c: c.name.lower()),
            'items': sorted(cat.get_items(), key=lambda i: i.name.lower()),
        }).reply(self)

class BrowserView(View):
    template_name = 'show_category.html'


class SubmitCategoryController(webapp.RequestHandler):
    def get(self):
        SubmitCategoryView({
            'category_name': self.request.get('name'),
        }).reply(self)

    def post(self):
        cat = Category()
        cat.name = self.request.get('name')
        cat.author = users.get_current_user()
        if self.request.get('link'):
            cat.link = self.request.get('link')
        cat.item_count = 0
        cat.put()
        self.redirect(os.environ['CAT_URL_PREFIX'] + '/' + cat.name)


class SubmitCategoryView(View):
    template_name = 'submit_category.html'


class SubmitItemController(webapp.RequestHandler):
    def get(self):  
        SubmitItemView({
            'category_name': self.request.get('cat'),
        }).reply(self)

    def post(self):
        item = CatItem()
        item.name = self.request.get('name')
        item.categories = split(self.request.get('cat'), ',')
        item.links = split(self.request.get('links'))
        item.put()
        self.redirect(item.categories[0])

class SubmitItemView(View):
    template_name = 'submit_item.html'


class ShowItemController(webapp.RequestHandler):
    def get(self, name):
        item = CatItem.get_by_name(name)
        if not item:
            raise NotFound
        ShowItemView({
            'item': item,
        }).reply(self)

class ShowItemView(View):
    template_name = 'show_item.html'


class IndexController(webapp.RequestHandler):
    def get(self):
        IndexView({
            'categories': Category.get_toc(),
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
        (prefix + '/submit', SubmitItemController),
        (prefix + '/submit/category', SubmitCategoryController),
        (prefix + '/v/(.*)', ShowItemController),
        (prefix + '/(.*)', BrowserController),
    ], debug=debug))


if __name__ == '__main__':
    serve('/c')
