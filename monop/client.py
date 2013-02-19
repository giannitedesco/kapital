#!/usr/bin/python

from linesock import LineSock
from xmlhelper import parse_xml_string
from collections import namedtuple

from gametype import GameType
from gameobj import GameObj
from fieldtype import *
from errors import *

class MonopPlayer(GameObj):
	__types = [FieldTypeInt('playerid', -1),
			FieldTypeInt('game', -1),
			FieldTypeStr('cookie'),
			FieldTypeStr('name'),
			FieldTypeStr('image'),
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

	def __init__(self):
		GameObj.__init__(self, MonopPlayer.__types)

class MonopGame(GameObj):
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
		GameObj.__init__(self, MonopGame.__types)

class EstateGroup(GameObj):
	__types = [FieldTypeInt('groupid', -1),
			FieldTypeStr('name')]
	def __init__(self):
		GameObj.__init__(self, EstateGroup.__types)

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

class Client:
	def quit(self):
		return

	def display(self, xml):
		self.dumpxml(xml)
		return

	def estategroup(self, xml):
		try:
			gid = int(xml['groupid'])
		except KeyError, ValueError:
			raise MonopError

		g = self.groups.get(gid, EstateGroup())
		g.update(xml)
		self.groups[g.groupid] = g

	def estate(self, xml):
		try:
			eid = int(xml['estateid'])
		except KeyError, ValueError:
			raise MonopError

		e = self.estates.get(eid, Estate())
		e.update(xml)
		self.estates[e.estateid] = e

	def configupdate(self, xml):
		#self.dumpxml(xml)
		return

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

	def gameupdate(self, xml):
		try:
			gid = int(xml['gameid'])
		except KeyError, ValueError:
			raise MonopError

		if gid < 0:
			return self.gametype(xml)

		g = self.games.get(gid, MonopGame())
		new = g.gameid == -1
		g.update(xml)

		self.games[g.gameid] = g

		self.msg('game update: ', ['bold'])
		self.msg('%s: %s\n'%(g.name,
			', '.join(['%s -> %s'%(k, v) for
				k,v in xml.attrib.items()])))

		if g.master == self.pid and g.description != 'robotwar':
			self.msg('I AM MASTER, SETTING NAME\n', ['dark green'])
			self.sock.send('.gd%s\n'%'robotwar')
		elif g.master == self.pid and g.players >= 2 \
				and g.status == 'config':
			self.msg('I AM MASTER, STARTING GAME\n', ['dark green'])
			self.sock.send('.gs\n')
		elif g.canbejoined and g.description == 'robotwar' and \
				self.players[self.pid].game == -1 and \
				g.status != 'config':
			self.msg('JOINING GAME\n', ['red'])
			self.sock.send('.gj%d\n'%g.gameid)

	def deleteplayer(self, xml):
		try:
			pid = int(xml['playerid'])
			p = self.players[pid]
			del self.players[pid]
		except KeyError, ValueError:
			raise MonopError

		self.msg('deleted player: ', ['bold'])
		self.msg('%s\n'%p.name)

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
			self.groups = {}
			self.estates ={}

	def playerupdate(self, xml):
		try:
			pid = int(xml['playerid'])
		except KeyError, ValueError:
			raise MonopError

		p = self.players.get(pid, MonopPlayer())
		new = p.playerid == -1

		p.update(xml)
		self.players[p.playerid] = p

		if new:
			self.msg('player: ', ['bold'])
			self.msg('%s\n'%p.name)
		else:
			self.msg('player update: ', ['bold'])
			self.msg('%s: %s\n'%(p.name,
				', '.join(['%s -> %s'%(k, v) for
					k,v in xml.attrib.items()])))

		if pid == self.pid and bool(int(xml.get('can_roll', 0))):
			self.msg('ROLLIN\n', ['purple'])
			self.sock.send('.r\n')

		if pid == self.pid and not self.ready:
			self.ready = True
			if self.nick == p.name:
				self.msg('I AM FIRST\n', ['dark green'])
				self.sock.send('.gn%s\n'%'london')
			else:
				self.msg('I AM SECOND\n', ['red'])

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
		self.sock.send('.n%s\n'%self.nick)

	def abort(self):
		self.sock = None
		self.pid = None
		self.cookie = None
		self.gametypes = {}
		self.games = {}
		self.groups = {}
		self.players = {}
		self.estates = {}
		self.ready = False

	def __init__(self, msg, nick = 'MrMonopoly'):
		self.msg = msg
		self.nick = nick
		self.abort()

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
					'client':self.client,
					'server':self.server,
					'display':self.display,
					'msg':self.svrmsg,
					'updategamelist':ignore,
					'playerupdate':self.playerupdate,
					'gameupdate':self.gameupdate,
					'deleteplayer':self.deleteplayer,
					'deletegame':self.deletegame,
					'configupdate':self.configupdate,
					'estategroupupdate':self.estategroup,
					'estateupdate':self.estate,
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

		self.sock = LineSock()
		self.sock.connect('data-in', sock_in)
		self.sock.connect('connected', connected)
		self.sock.connect('disconnected', disconnected)
		self.sock.connect('error', sockerr)
		self.sock.connect_to(host, port)
