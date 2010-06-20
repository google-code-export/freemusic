# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging

import base
import model

class Editor(base.BaseRequestHandler):
	def get(self):
		obj = model.db.get(model.db.Key(self.request.get('key')))
		self.send_html('editor.html', {
			'next': self.request.get('next'),
			'object': obj,
			'fields': self.get_form(obj),
		})

	def get_form(self, obj):
		fields = []
		json = obj.to_json()
		for k in json:
			fields.append({
				'name': k,
				'value': json[k],
			})
		return fields

	def post(self):
		obj = model.db.get(model.db.Key(self.request.get('_key')))
		json = dict([(arg, self.request.get(arg)) for arg in self.request.arguments() if arg in obj.fields()])
		obj.from_json(json).put()
		self.redirect(self.request.get('_next'))

if __name__ == '__main__':
	base.run([
		('/edit', Editor),
	])
