# vim: set ts=4 sts=4 sw=4 et fileencoding=utf-8:

# Python imports.
import urllib

# GAE imports.
from google.appengine.ext import webapp

register = webapp.template.create_template_register()

@register.filter
def uurlencode(value):
    if type(value) == unicode:
        value = value.encode('utf-8')
    return urllib.quote(value)

@register.filter
def hostname(value):
    host = value.split('/')[2]
    if host.startswith('www.'):
        host = host[4:]
    return host
