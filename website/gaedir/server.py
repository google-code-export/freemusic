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


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def split(value, sep='\n'):
    return [p.strip() for p in value.split(sep) if p.strip()]


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

    @classmethod
    def find_all(cls, limit=1000, order=None):
        query = cls.all()
        if order is not None:
            query = query.order(order)
        return query.fetch(limit)


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
        if parents:
            self.first_parent = max(parents)

        self.update_item_count()

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

        children = [c for c in children if c.item_count > 0]
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
        self.item_count = GAEDirEntry.gql('WHERE all_categories = :1', self.name).count()

    def __repr__(self):
        return u'<gaedir.Category name=%s promote=%s>' % (self.name, self.promote or False)

    def schedule_update(self):
        """Starts background update of the category."""
        taskqueue.add(url=os.environ['CAT_URL_PREFIX'] + '/update/category', params={'key': str(self.key())})

    def is_shown_in_toc(self):
        return self.item_count > 0

    @classmethod
    def get_by_name(cls, name):
        cat = cls.gql('WHERE name = :1', name.strip()).get()
        return cat

    @classmethod
    def get_toc(cls):
        """Returns a structure with the top categories, to show on the front
        page.  The structure is a list of (name, children)."""
        toc = []
        categories = cls.gql('WHERE depth < 3').fetch(1000)

        for cat in categories:
            if cat.depth == 1 and cat.is_shown_in_toc():
                promoted = []
                normal = []
                for sub in categories:
                    if cat.is_shown_in_toc():
                        if cat.name in sub.parents:
                            if sub.promote:
                                promoted.append(sub)
                            else:
                                normal.append(sub)

                limit = max(4, len(promoted))
                children = promoted + normal

                toc.append({
                    'name': cat.name,
                    'children': sorted(children[:limit], key=lambda c: c.name.lower()),
                })

        return sorted(toc, key=lambda x: x['name'].lower())

    @classmethod
    def update_some(cls, names):
        """Schedules updates of the specified categories."""
        for name in names:
            cat = cls.get_by_name(name)
            if cat is not None:
                cat.schedule_update()


class GAEDirEntry(Model):
    name = db.StringProperty()
    categories = db.StringListProperty()
    links = db.StringListProperty()
    picture = db.LinkProperty()
    description = db.TextProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)

    # Used by the cron job to update information from external sources.
    last_updated = db.DateTimeProperty(auto_now_add=True)

    # This includes implicitly added parent categories.
    all_categories = db.StringListProperty()

    def put(self):
        self.update_all_categories()
        # self.update_counts()
        db.Model.put(self)

    def schedule_update(self):
        """Starts background update of the entry."""
        taskqueue.add(url=os.environ['CAT_URL_PREFIX'] + '/update/entry', params={'key': str(self.key())})

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
        return cls.gql('WHERE name = :1', name.strip()).get()

    @classmethod
    def get_by_category(cls, name, limit=100):
        return cls.gql('WHERE all_categories = :1', name).fetch(limit)


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
        self.data['base'] = self.get_base_url()
        if self.data['user']:
            self.data['log_out_url'] = users.create_logout_url(os.environ['PATH_INFO'])
        else:
            self.data['log_in_url'] = users.create_login_url(os.environ['PATH_INFO'])

        path = os.path.join(os.path.dirname(__file__), 'templates', self.template_name)
        content = template.render(path, self.data)

        request.response.headers['Content-Type'] = self.content_type + '; charset=utf-8'
        request.response.out.write(content)

    def get_base_url(self):
        """Returns the base for all URLs."""
        base = 'http://' + os.environ['HTTP_HOST']
        if base.endswith(':80'):
            base = base[:-3]
        base += os.environ['CAT_URL_PREFIX']
        return base


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
    template_name = 'submit_entry.html'


class ShowItemController(Controller):
    def get(self, name):
        item = GAEDirEntry.get_by_name(url_unquote(name))
        if not item:
            raise NotFound
        ShowItemView({
            'item': item,
        }).reply(self)


class ShowItemView(View):
    template_name = 'show_entry.html'

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

        categories = item.categories

        item.update({
            'name': self.request.get('name'),
            'categories': split(self.request.get('categories'), '\n'),
            'links': split(self.request.get('links'), '\n'),
            'picture': self.request.get('picture'),
            'description': self.request.get('description'),
        })
        item.put()
        item.schedule_update()

        GAEDirCategory.update_some(add_parents(categories + item.categories))

        self.redirect('/v/' + item.name.encode('utf-8'))


class EditEntryView(View):
    template_name = 'edit_entry.html'


class IndexController(webapp.RequestHandler):
    def get(self):
        IndexView({
            'toc': GAEDirCategory.get_toc(),
        }).reply(self)


class IndexView(View):
    template_name = 'index.html'


class UpdateEntryController(Controller):
    def get(self):
        entries = GAEDirEntry.find_all()
        for entry in entries:
            entry.schedule_update()
        return 'Scheduled update of %u entries.' % len(entries)

    def post(self):
        entry = GAEDirEntry.get_by_key(self.request.get('key'))
        if not entry:
            raise NotFound
        """
        if not users.is_current_user_admin():
            raise Forbidden
        """

        update = self.update_from_lastfm(entry)
        if entry.date_added > entry.last_updated:
            update = True
        if update:
            entry.put()

    def update_from_lastfm(self, entry):
        update = False
        for link in entry.links:
            match = re.match('http://(?:www.last.fm|www.lastfm.ru)/music/(.+)', link)
            if match:
                url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=%s&api_key=%s&format=json' % (match.group(1), LAST_FM_KEY)
                data = simplejson.loads(urlfetch.fetch(url=url).content)

                if not entry.picture:
                    for image in data['artist']['image']:
                        if image['size'] == 'large':
                            entry.picture = image['#text']
                            logging.info(u'Found picture for %s: %s' % (entry.name, entry.picture))
                            update = True

                try:
                    if not entry.description:
                        entry.description = HTMLStripper.process(data['artist']['bio']['content'])
                except KeyError:
                    pass
        return update


class UpdateCategoryController(Controller):
    def get(self):
        for cat in GAEDirCategory.find_all():
            cat.schedule_update()

    def post(self):
        cat = GAEDirCategory.get_by_key(self.request.get('key'))
        if not cat:
            raise NotFound
        logging.debug(u'Updating category %s' % cat.name)
        cat.put()


class SitemapController(Controller):
    def get(self):
        SitemapView({
            'categories': GAEDirCategory.find_all('name'),
            'entries': GAEDirEntry.find_all('name'),
        }).reply(self)


class SitemapView(View):
    template_name = 'sitemap.xml'


class RobotsController(Controller):
    def get(self):
        RobotsView().reply(self)


class RobotsView(View):
    template_name = 'robots.txt'
    content_type = 'text/plain'


class CategoriesFeedController(Controller):
    def get(self):
        CategoriesFeedView({
            'categories': GAEDirCategory.find_all(limit=100, order='-date_added'),
        }).reply(self)


class CategoriesFeedView(View):
    template_name = 'categories.rss'
    content_type = 'application/rss+xml'


class EntriesFeedController(Controller):
    def get(self):
        if self.request.get('category'):
            data = GAEDirEntry.get_by_category(self.request.get('category'), limit=100)
        else:
            data = GAEDirEntry.find_all(limit=100, order='-date_added')
        logging.debug(data)
        EntriesFeedView({
            'entries': data,
        }).reply(self)


class EntriesFeedView(View):
    template_name = 'entries.rss'
    content_type = 'application/rss+xml'


def serve(prefix=''):
    debug = True
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    os.environ['CAT_URL_PREFIX'] = prefix
    webapp.template.register_template_library('gaedir.filters')
    wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
        (prefix + '/', IndexController),
        (prefix + '/edit/category', EditCategoryController),
        (prefix + '/edit/entry', EditEntryController),
        (prefix + '/export/categories\.rss', CategoriesFeedController),
        (prefix + '/export/entries\.rss', EntriesFeedController),
        (prefix + '/robots\.txt', RobotsController),
        (prefix + '/sitemap\.xml', SitemapController),
        (prefix + '/submit', SubmitEntryController),
        (prefix + '/update/category', UpdateCategoryController),
        (prefix + '/update/entry', UpdateEntryController),
        (prefix + '/v/(.*)', ShowItemController),
        (prefix + '/(.*)', ShowCategoryController),
    ], debug=debug))


if __name__ == '__main__':
    serve('/c')
