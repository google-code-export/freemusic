# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import sys

import jabberbot

class FMHBot(jabberbot.JabberBot):
    pass

def run(settings):
    if settings['jabber'] is None:
        print >>sys.stderr, 'No jabber settings (jabber.login, jabber.password)'
        sys.exit(1)
    bot = FMHBot(settings['jabber']['login'], settings['jabber']['password'])
    bot.serve_forever()
