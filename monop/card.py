from gameobj import GameObj
from fieldtype import *

class Card(GameObj):
	__types = [FieldTypeInt('advanceto', -1),
			FieldTypeInt('advance', 0),
			FieldTypeInt('pay', -1),
			FieldTypeInt('payhouse', -1),
			FieldTypeInt('payhotel', -1),
			FieldTypeInt('payeach', -1),
			FieldTypeBool('tojail', False),
			FieldTypeBool('canbeowned', False),
			FieldTypeBool('outofjail', False),
			FieldTypeStr('advancetonextof'),
			FieldTypeStr('rentmath'),
			FieldTypeStr('name')]
	def __init__(self):
		GameObj.__init__(self, Card.__types)
