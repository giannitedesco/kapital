import gobject, glib

from gametype import GameType
from gameobj import GameObj
from fieldtype import *
from game import Game
from player import Player
from estategroup import EstateGroup
from estate import Estate
from errors import *

class Strategy(gobject.GObject):
	__gsignals__ = {
		'msg': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_STRING,
						gobject.TYPE_PYOBJECT)),
	}
	def msg(self, s, tags = []):
		self.emit('msg', s, tags)
	def __init__(self):
		super(Strategy, self).__init__()

gobject.type_register(Strategy)
