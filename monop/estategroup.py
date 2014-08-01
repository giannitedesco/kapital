from gameobj import GameObj
from fieldtype import *

class EstateGroup(GameObj):
	__types = [FieldTypeInt('groupid', -1),
			FieldTypeInt('houseprice', -1),
			FieldTypeInt('price', -1),
			FieldTypeStr('rentmath'),
			FieldTypeStr('name'),
			FieldTypeStr('color')]
	def __init__(self):
		GameObj.__init__(self, EstateGroup.__types)
		object.__setattr__(self, 'estates', set())
