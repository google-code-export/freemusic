import datetime

from google.appengine.api import users
from django.utils import simplejson

class Encoder(simplejson.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'to_dict'):
            return getattr(o, 'to_dict')()

        typ = type(o)
        if typ == datetime.datetime:
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if typ == datetime.date:
            return o.strftime('%Y-%m-%d')
        if typ == users.User:
            return o.email()

        return super(Encoder, self).default(o)


def dump(response, obj):
    result = simplejson.dumps(obj, indent=True, cls=Encoder)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.out.write(result)
