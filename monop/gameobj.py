from collections import namedtuple

Field = namedtuple('Field', ['type', 'value'])
class GameObj(object):
	def __init__(self, types, updated = None):
		object.__setattr__(self, '_GameObj__fields', {})
		object.__setattr__(self, 'updated', updated)
		for t in types:
			self.__fields[t.name] = Field(t, t.default)
		if self.updated:
			self.updated(self, None, None)

	def __dir__(self):
		return self.__fields.keys()

	def __getattr__(self, attr):
		if self.__fields.has_key(attr):
			return self.__fields[attr].value
		else:
			raise AttributeError

	def __setattr__(self, attr, val):
		if self.__fields.has_key(attr):
			a = self.__fields[attr]
			v = a.type.validate(val)
			self.__fields[attr] = Field(a.type, v)
			if self.updated is not None:
				self.updated(self, attr, v)
		else:
			raise AttributeError, '%s not found'%attr

	def update(self, xml):
		for (k,v) in xml.attrib.items():
			try:
				setattr(self, k, v)
			except AttributeError:
				print 'BAD ATTRIBUTE', k, v
				raise AttributeError
