from gameobj import GameObj
from fieldtype import *

class Estate(GameObj):
	__types = [FieldTypeInt('estateid', -1),
			FieldTypeInt('unmortgageprice'),
			FieldTypeInt('mortgageprice'),
			FieldTypeInt('rent0'),
			FieldTypeInt('rent1'),
			FieldTypeInt('rent2'),
			FieldTypeInt('rent3'),
			FieldTypeInt('rent4'),
			FieldTypeInt('rent5'),
			FieldTypeInt('houses'),
			FieldTypeInt('houseprice'),
			FieldTypeInt('sellhouseprice'),
			FieldTypeInt('price'),
			FieldTypeInt('payamount'),
			FieldTypeInt('money'),
			FieldTypeInt('passmoney'),
			FieldTypeInt('taxpercentage'),
			FieldTypeInt('tax'),
			FieldTypeInt('group', -1),
			FieldTypeInt('owner', -1),
			FieldTypeBool('can_toggle_mortgage'),
			FieldTypeBool('can_sell_houses'),
			FieldTypeBool('can_buy_houses'),
			FieldTypeBool('can_be_owned'),
			FieldTypeBool('tojail'),
			FieldTypeBool('mortgaged'),
			FieldTypeBool('jail'),
			FieldTypeStr('icon'),
			FieldTypeStr('color'),
			FieldTypeStr('bgcolor'),
			FieldTypeStr('name')]
	def __init__(self):
		GameObj.__init__(self, Estate.__types)
