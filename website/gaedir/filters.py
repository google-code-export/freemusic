import os
import urllib

from google.appengine.ext import webapp

register = webapp.template.create_template_register()


@register.filter
def catname(name):
    return name.replace('/', ': ')


@register.filter
def catlink(name):
    parts = name.split(u'/')
    result = u'<a href="%s/%s">%s</a>' % (os.environ['CAT_URL_PREFIX'], name.replace(' ', '_'), parts[-1])
    if len(parts) > 1:
        result = catlink(u'/'.join(parts[:-1])) + u': ' + result
    return result
