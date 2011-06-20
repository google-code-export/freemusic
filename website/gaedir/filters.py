import cgi
import os
import urllib

from google.appengine.ext import webapp

register = webapp.template.create_template_register()


@register.filter
def catname(name):
    return name.replace('/', ': ')


@register.filter
def uurlencode(url):
    return urllib.quote(url.replace(' ', '_').encode('utf-8'))


@register.filter
def catlink(name):
    parts = name.split(u'/')
    result = u'<a href="%s/%s">%s</a>' % (os.environ['CAT_URL_PREFIX'], name.replace(' ', '_'), parts[-1])
    if len(parts) > 1:
        result = catlink(u'/'.join(parts[:-1])) + u': ' + result
    return result


@register.filter
def shortcatlink(name):
    text = name.split(u'/')[-1]
    result = u'<a href="%s/%s">%s</a>' % (os.environ['CAT_URL_PREFIX'], name.replace(' ', '_'), text)
    return result


@register.filter
def simplecatlink(name):
    text = name.replace('/', ': ')
    link = os.environ['CAT_URL_PREFIX'] + '/' + name.replace(' ', '_')
    return u'<a href="%s" class="category">%s</a>' % (link, text)


@register.filter
def listarea(values):
    return u'\n'.join(sorted(values))


@register.filter
def safe_html(text):
    text = cgi.escape(text).replace('&lt;p&gt;', '<p>').replace('&lt;/p&gt;', '</p>')
    return text
