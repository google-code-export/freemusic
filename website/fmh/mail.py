import logging
import os

from google.appengine.api import mail

from fmh import view


def send(to, template_name, data=None):
    data = data or {}
    data['base_url'] = 'http://' + os.environ['SERVER_NAME']
    if os.environ['SERVER_PORT'] != '80':
        data['base_url'] += ':' + os.environ['SERVER_PORT']

    text = view.Base().render_template(template_name, data)
    mail.send_mail(sender='me@example.com', to=to, subject='Hello, world!', body='See HTML.', html=text.strip())
