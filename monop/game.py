from gameobj import GameObj
from fieldtype import *

class Game(GameObj):
	__types = [FieldTypeInt('gameid', -1),
			FieldTypeStr('gametype'),
			FieldTypeStr('name'),
			FieldTypeStr('description'),
			FieldTypeStr('status'),
			FieldTypeInt('players'),
			FieldTypeInt('minplayers'),
			FieldTypeInt('maxplayers'),
			FieldTypeBool('canbejoined'),
			FieldTypeBool('allowestatesales'),
			FieldTypeBool('collectfines'),
			FieldTypeBool('alwaysshuffle'),
			FieldTypeBool('auctionsenabled'),
			FieldTypeBool('doublepassmoney'),
			FieldTypeBool('unlimitedhouses'),
			FieldTypeBool('norentinjail'),
			FieldTypeInt('master')]
	def __init__(self):
		GameObj.__init__(self, Game.__types)

