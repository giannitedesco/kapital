import gobject, glib

from linesock import LineSock
from xmlhelper import parse_xml_string
from collections import namedtuple

from gametype import GameType
from gameobj import GameObj
from fieldtype import *
from game import Game
from player import Player
from estategroup import EstateGroup
from estate import Estate
from gamestate import GameState
from errors import *

class Client(gobject.GObject):
	__gsignals__ = {
		'msg': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_STRING,
						gobject.TYPE_PYOBJECT)),
		'updated': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, ()),
	}

	def msg(self, s, tags = []):
		self.emit('msg', s, tags)

	def cmd(self, s):
		#from time import sleep
		if self.sock is None:
			return
		self.sock.send('%s\n'%s)
		self.msg('<< %s\n'%s, ['blue'])
		#sleep(0.5)

	def roll(self):
		# do stuff
		self.msg('ROLLIN\n', ['red'])
		self.cmd('.r')

	def do_turn(self, i):
		if i.hasdebt:
			self.strategy.handle_debt(i)
			self.roll()
		elif i.can_buyestate:
			self.strategy.handle_purchase(i)
		elif i.jailed:
			self.strategy.handle_jail(i)
		elif len(self.buttons) and not i.can_buyestate:
			self.msg('%r\n'%self.buttons, ['red'])
			self.strategy.handle_tax(i)
		elif i.can_roll or i.canrollagain:
			self.strategy.manage_estates(i)
			self.roll()

	def display(self, xml):
		try:
			text = xml.get('text', '')
			cleartext = bool(int(xml.get('cleartext', 0)))
			clearbuttons = bool(int(xml.get('clearbuttons', 0)))
			estateid = int(xml.get('estateid', -1))
		except KeyError, ValueError:
			raise MonopError

		if clearbuttons:
			self.buttons = []

		if self.disp is None:
			self.msg('%s\n'%text)
		else:
			self.disp.display(text = text, cleartext = cleartext,
				clearbuttons = clearbuttons,
				estateid = estateid)
			self.msg('%s\n'%text)

		for x in xml.children:
			if x.name != 'button':
				continue
			caption = x.get('caption', '')
			command = x.get('command', '')
			enabled = bool(int(x.get('enabled', 1)))
			self.buttons.append((caption, command, enabled))
			self.disp.add_button(caption, command, enabled)

	def svrmsg(self, xml):
		try:
			t = xml['type']
			pid = int(xml.get('playerid', -1))
			author = xml.get('author', '')
			val = xml.get('value','')
		except KeyError, ValueError:
			raise MonopError
		self.msg('%s: %d: %s\n'%(t, pid, val), ['purple'])

	def gametype(self, xml):
		try:
			t = GameType(gameid = int(xml['gameid']),
				name = xml.get('name', None),
				gametype = xml.get('gametype', None),
				desc = xml.get('description',''),
				canbejoined = bool(xml.get('canbejoined',
							False)),
				minplayers = int(xml.get('minplayers', 0)),
				maxplayers = int(xml.get('maxplayers', 0)),
				players = int(xml.get('players', 0)),
				master = int(xml.get('master', -1)))
		except KeyError, ValueError:
			raise MonopError
		self.gametypes[t.name] = t
		self.msg('gametype: ', ['bold'])
		self.msg('%s, %s, %s\n'%(t.name, t.gametype, t.desc))

	def game_status_update(self, g, v):
		if v == 'config':
			def state_msg(it, *_):
				self.msg(*_)

			self.s = GameState()
			self.s.connect('msg', state_msg)
		elif v == 'init':
			p = filter(lambda x:x.game == g.gameid,
					self.players.values())
			self.s.game_init(p)
		elif v == 'run':
			self.strategy.game_on(self.s)
		elif v == 'end':
			self.strategy.game_over()
			self.s.game_over()

	def on_game_update(self, g, k, v):
		if k == 'status':
			self.game_status_update(g, v)

	def gameupdate(self, xml):
		try:
			gid = int(xml['gameid'])
		except KeyError, ValueError:
			raise MonopError

		if gid < 0:
			return self.gametype(xml)

		g = self.games.pop(gid, Game(self.on_game_update))
		new = g.gameid == -1
		g.update(xml)
		self.games[g.gameid] = g

		#self.msg('game update: ', ['bold'])
		#self.msg('%s: %s\n'%(g.name,
		#	', '.join(['%s -> %s'%(k, v) for
		#		k,v in xml.attrib.items()])))

		if g.master == self.pid and g.description != 'robotwar':
			self.msg('I AM MASTER, SETTING NAME\n', ['dark green'])
			self.cmd('.gd%s'%'robotwar')
		elif g.master == self.pid and g.players >= 2 \
				and g.status == 'config':
			self.msg('I AM MASTER, STARTING GAME\n', ['dark green'])
			self.cmd('.gs')
		elif g.canbejoined and g.description == 'robotwar' and \
				self.players[self.pid].game == -1 and \
				g.status != 'config':
			self.msg('JOINING GAME\n', ['red'])
			self.cmd('.gj%d'%g.gameid)

	def deletegame(self, xml):
		try:
			gid = int(xml['gameid'])
			g = self.games[gid]
			del self.games[gid]
		except KeyError, ValueError:
			raise MonopError

		self.msg('deleted game: ', ['bold'])
		self.msg('%s\n'%g.description)

		if self.players[self.pid].game == gid:
			self.abortgame()

	def on_player_update(self, p, k, v):
		if k == 'location':
			self.cmd('.t%d'%v)

		if k in ['hasturn', 'can_buyestate', 'hasdebt',
				'can_roll', 'canrollagain'] and v:
			if self.current != p or p.hasturn:
				self.newturn = True
			self.current = p

		if p.playerid == self.pid and k == 'name':
			self.svrnick = v

		#self.msg('%s: %s -> %s\n'%(p.name, k, v), ['purple'])

		if k == 'location':
			self.msg('%s now at %d\n'%(p.name, p.location))
		elif k == 'image':
			self.msg('%s now using avatar %s\n'%(p.name, p.image))
		elif k == 'game':
			gid = int(v)
		else:
			return

	def playerupdate(self, xml):
		try:
			pid = int(xml['playerid'])
		except KeyError, ValueError:
			raise MonopError

		p = self.players.pop(pid, Player(self.on_player_update))
		p.update(xml)
		self.players[p.playerid] = p

		if pid == self.pid and not self.ready:
			self.ready = True
			if self.nick == self.svrnick:
				self.msg('I AM FIRST\n', ['dark green'])
				self.cmd('.gn%s'%'london')
				self.cmd('.pi%s'%'hamburger.png')
			else:
				self.msg('I AM SECOND\n', ['red'])
				self.cmd('.pi%s'%'lips.png')

		if self.s is None or self.s.over:
			return
		if self.newturn or (len(self.buttons) and \
					not self.current.can_buyestate):
			if self.current.playerid == self.pid:
				self.do_turn(self.current)
				self.newturn = False

	def deleteplayer(self, xml):
		try:
			pid = int(xml['playerid'])
			p = self.players[pid]
			del self.players[pid]
		except KeyError, ValueError:
			raise MonopError

		self.msg('deleted player: ', ['bold'])
		self.msg('%s\n'%p.name)

	def estategroup(self, xml):
		self.s.estategroup(xml)
	def estate(self, xml):
		self.s.estate(xml)
	def configupdate(self, xml):
		self.s.configupdate(xml)
	def cardupdate(self, xml):
		self.s.cardupdate(xml)
	def auctionupdate(self, xml):
		self.s.auctionupdate(xml)

	def client(self, xml):
		try:
			pid = int(xml['playerid'])
			cookie = xml['cookie']
		except KeyError, ValueError:
			raise MonopError

		self.msg('playerid %d, cookie = \'%s\'\n'%(pid, cookie))
		self.pid = pid
		self.cookie = cookie

	def server(self, xml):
		try:
			ver = xml['version']
		except KeyError:
			raise MonopError
		self.msg('server version: %s\n'%ver)
		self.cmd('.n%s'%self.nick)

	def abortgame(self):
		self.current = None
		self.newturn = False
		self.buttons = []
		self.ready = False
		self.s = None

	def abort(self):
		self.sock = None
		self.pid = None
		self.cookie = None
		self.gametypes = {}
		self.games = {}
		self.players = {}
		self.svrnick = None
		self.abortgame()

	def __init__(self, disp = None, nick = 'MrMonopoly', strategy = None):
		gobject.GObject.__init__(self)

		self.disp = disp
		self.nick = nick
		self.abort()

		def strategy_msg(it, *_):
			self.msg(*_)
		def strategy_cmd(it, *_):
			self.cmd(*_)
		strategy.connect('msg', strategy_msg)
		strategy.connect('cmd', strategy_cmd)
		self.strategy = strategy

	def dumpxml(self, n, depth = 0):
		"Dump a XMLNode DOM"

		def indent(depth):
			return ''.join([' ' for x in xrange(depth)])
		self.msg('%s+ %s\n'%(indent(depth), n.name))
		for (k, v) in n.attrib.items():
			self.msg('%s - %s = %s\n'%(indent(depth), k, v))
		if n.text is not None:
			self.msg('%so %s\n'%(indent(depth), n.text))
		for x in n.children:
			self.dumpxml(x, depth + 1)

	def connect_to(self, host, port):
		def sockerr(sock, op, msg):
			self.msg('*** %s: %s:%d: %s\n'%(op,
					sock.peer[0],
					sock.peer[1],
					msg), ['bold', 'purple'])
			self.abort()

		def connected(sock):
			self.msg('*** Connected: %s:%d\n'%(
					sock.peer[0],
					sock.peer[1]), ['bold', 'purple'])

		def disconnected(sock):
			self.msg('*** Disonnected: %s:%d\n'%(
					sock.peer[0],
					sock.peer[1]), ['bold', 'purple'])
			self.abort()

		def sock_in(sock, msg):
			def transition(xml):
				def ignore(xml):
					return
				disp = {
					# login stuff
					'client':self.client,
					'server':self.server,

					# lobby stuff
					'gameupdate':self.gameupdate,
					'updategamelist':ignore,
					'deletegame':self.deletegame,

					# misc
					'display':self.display,
					'msg':self.svrmsg,

					# both lobby and game
					'playerupdate':self.playerupdate,
					'deleteplayer':self.deleteplayer,

					# gamestate relevant
					'configupdate':self.configupdate,
					'estategroupupdate':self.estategroup,
					'estateupdate':self.estate,
					'cardupdate':self.cardupdate,
					'auctionupdate':self.auctionupdate,
				}
				if xml.name != 'monopd':
					raise MonopError
				for x in xml.children:
					disp.get(x.name, self.dumpxml)(x)

			try:
				xml = parse_xml_string(msg)
			except:
				self.msg('Barfed on XML: %s\n'%msg, ['red'])
			try:
				transition(xml)
			except MonopError, e:
				self.msg('Barfed on message:\n', ['red'])
				self.dumpxml(xml)
				self.abort()
			self.emit('updated')

		self.sock = LineSock()
		self.sock.connect('data-in', sock_in)
		self.sock.connect('connected', connected)
		self.sock.connect('disconnected', disconnected)
		self.sock.connect('error', sockerr)
		self.sock.connect_to(host, port)

gobject.type_register(Client)
