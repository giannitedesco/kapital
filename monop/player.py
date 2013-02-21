from gameobj import GameObj
from fieldtype import *

class Player(GameObj):
	__types = [FieldTypeInt('playerid', -1),
			FieldTypeInt('game', -1),
			FieldTypeStr('cookie'),
			FieldTypeStr('name'),
			FieldTypeStr('image', 'badge.png'),
			FieldTypeStr('money'),
			FieldTypeInt('location'),
			FieldTypeInt('doublecount'),
			FieldTypeInt('jailcount'),
			FieldTypeBool('jailed'),
			FieldTypeBool('directmove'),
			FieldTypeBool('bankrupt'),
			FieldTypeBool('hasturn'),
			FieldTypeBool('can_roll', 0),
			FieldTypeBool('canrollagain', 0),
			FieldTypeBool('can_buyestate', 0),
			FieldTypeStr('host'),
			FieldTypeBool('spectator'),
			FieldTypeBool('hasdebt'),
			FieldTypeBool('master'),
			FieldTypeBool('canauction'),
			FieldTypeBool('canusecard')]

	def __init__(self, updated = None):
		GameObj.__init__(self, Player.__types, updated)
