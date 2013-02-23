from gameobj import GameObj
from fieldtype import *

class EstateGroup(GameObj):
	__types = [FieldTypeInt('groupid', -1),
			FieldTypeStr('name')]
	def __init__(self):
		GameObj.__init__(self, EstateGroup.__types)
		object.__setattr__(self, 'estates', set())
