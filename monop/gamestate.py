import gobject, glib
from player import Player
from estategroup import EstateGroup
from estate import Estate
from errors import *

class GameState(gobject.GObject):
	__gsignals__ = {
		'msg': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_STRING,
						gobject.TYPE_PYOBJECT)),
	}

	def msg(self, s, tags = []):
		self.emit('msg', s, tags)

	def game_init(self, players):
		self.players = {}
		self.groups = {}
		self.estates = {}

		for p in players:
			self.players[p.playerid] = p

	def game_on(self):
		self.emap = {}
		for k,v in self.groups.items():
			s = frozenset(map(lambda x:x.estateid,
					filter(lambda x:x.group == k,
					self.estates.values())))
			self.emap[k] = s

	def __init__(self):
		super(GameState, self).__init__()
		self.over = False
	
	def game_over(self):
		self.over = True

	def estategroup(self, xml):
		try:
			gid = int(xml['groupid'])
		except KeyError, ValueError:
			raise MonopError

		g = self.groups.pop(gid, EstateGroup())
		g.update(xml)
		self.groups[g.groupid] = g

	def estate(self, xml):
		try:
			eid = int(xml['estateid'])
		except KeyError, ValueError:
			raise MonopError

		e = self.estates.pop(eid, Estate())
		e.update(xml)
		self.estates[e.estateid] = e

	def configupdate(self, xml):
		# TODO: strategy needs to know
		return

	def cardupdate(self, xml):
		try:
			owner = int(xml.get('owner', -1))
			cardid = int(xml.get('cardid', -1))
		except KeyError, ValueError:
			raise MonopError
		self.msg('player %d gets card %d\n'%(owner, cardid), ['purple'])

	def auctionupdate(self, xml):
		#self.dumpxml(xml)
		return

gobject.type_register(GameState)
