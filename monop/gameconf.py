from player import Player
from estategroup import EstateGroup
from estate import Estate
from monop.card import Card
from errors import *

class GameConf(object):
	JAIL_ROLLS = 3

	def load(self, f):
		self.groupidx = {}
		self.groups = []
		self.estates = []
		self.cards = {}
		self.params = {}
		self.jail = 10
		self.tojail = 30
		def General(params, sec):
			for k,v in params:
				self.params[k] = v
		def EstateGroups(params, secs):
			for h, b in secs:
				g = EstateGroup()
				g.name = h
				for k, v in b:
					setattr(g, k, v)
				self.groupidx[g.name] = len(self.groups)
				self.groups.append(g)

		def Estates(params, secs):
			for h, b in secs:
				e = Estate()
				e.name = h
				for k, v in b:
					if k == 'group':
						v = self.groupidx.get(v, -1)
					setattr(e, k, v)
				if e.jail:
					self.jail = len(self.estates)
				if e.tojail:
					self.tojail = len(self.estates)
				self.estates.append(e)

		def Cards(params, secs):
			gn = None
			for k,v in params:
				if k == 'groupname':
					gn = v
			for h,b in secs:
				c = Card()
				c.name = h
				for k, v in b:
					setattr(c, k, v)
				self.cards.setdefault(gn, list()).append(c)


		params = []
		secs = []
		k = None
		vals = []
		sec = None
		while True:
			l = f.readline()
			if l == '':
				break
			l = l.rstrip('\r\n')
			if l == '':
				continue
			if l[0] == '#':
				continue

			sections = {
				'<General>':General,
				'<EstateGroups>':EstateGroups,
				'<Board>':None,
				'<Cards>':Cards,
				'<Estates>':Estates,
			}
			if l[0] == '<':
				if k is None:
					params.extend(vals)
				else:
					secs.append((k, vals))
				vals = []
				k = None
				if sec is not None:
					sec(params, secs)
				params = []
				secs = []
				sec = sections.get(l, None)
			elif l[0] == '[':
				if k is None:
					params.extend(vals)
				else:
					secs.append((k, vals))
				vals = []
				k = l[1:-1]
			else:
				arr = l.split('=')
				assert(len(arr) == 2)
				vals.append((arr[0], arr[1]))
		secs.append((k, vals))
		if sec is not None:
			sec(params, secs)

	def __init__(self, f = None):
		super(GameConf, self).__init__()
		self.groups = []
		self.estates = []
		if f is not None:
			self.load(f)
