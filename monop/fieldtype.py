class FieldType:
	def __init__(self, name, default = None):
		self.name = name
		self.default = default
	def validate(self, val):
		return val

class FieldTypeInt(FieldType):
	def __init__(self, name, default = 0):
		FieldType.__init__(self, name, default)
	def validate(self, val):
		return int(val)
class FieldTypeStr(FieldType):
	def __init__(self, name, default = ''):
		FieldType.__init__(self, name, default)
	def validate(self, val):
		return str(val)
class FieldTypeBool(FieldType):
	def __init__(self, name, default = False):
		FieldType.__init__(self, name, default)
	def validate(self, val):
		return bool(int(val))
