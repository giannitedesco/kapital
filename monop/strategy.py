import gobject, glib

class Strategy(gobject.GObject):
	__gsignals__ = {
		'msg': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_STRING,
						gobject.TYPE_PYOBJECT)),
		'mortgage': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_INT,)),
		'unmortgage': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_INT,)),
		'sell-house': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_INT,)),
		'buy-house': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_INT,)),
	}
	def msg(self, s, tags = []):
		self.emit('msg', s, tags)
	def mortgage(self, estateid): 
		self.emit('mortgage', estateid)
	def unmortgage(self, estateid): 
		self.emit('unmortgage', estateid)
	def sell_house(self, estateid): 
		self.emit('sell-house', estateid)
	def buy_house(self, estateid): 
		self.emit('buy-house', estateid)

	def __init__(self):
		super(Strategy, self).__init__()
		self.s = None

	def game_on(self, state):
		self.s = state

	def game_over(self):
		# maybe save some win/loss stats?
		return

	def split_hand(self, hand):
		out = []

		# first build a set of estates in our hand
		s = set(map(lambda x:x.estateid, hand))

		# keep track of properties part of monopolies
		mprops = set()

		for g in self.s.groups.values():
			# if the intersection of estates in a group is
			# equal to the set of all estates in a group then
			# we have a monopoly
			m = self.s.emap.get(g.groupid, frozenset())
			if s.intersection(m) == m:
				# so lets lookup all the estate objects
				e = map(lambda x:self.s.estates[x], sorted(m))

				# then append them to our results
				out.append(e)

				# and keep track of what we appended
				mprops |= set(m)

		# so that we can build a list of the remainder
		misc = map(lambda x:self.s.estates[x],s - mprops)

		return (out, misc)

	def hand(self, p):
		return filter(lambda x:x.owner == p.playerid,
				self.s.estates.values())

	def due(self, p, e):
		self.msg('due %r\n'%e)
		if e.owner == p.playerid:
			self.msg('we own this?!\n')
			return 0
		price = getattr(e, 'rent%d'%e.houses)
		if price >= 0:
			self.msg('so that\'s %d\n'%price)
			return price
		if e.tax:
			self.msg('it\'s a tax of %%d\n'%e.tax)
			return e.tax
		return 0

	def handle_debt(self, p):
		raise NotImplemented

	def handle_purchase(self, p):
		raise NotImplemented

	def remain_in_jail(self, i):
		raise NotImplemented

	def pay_asset_tax(self, p):
		raise NotImplemented

	def manage_estates(self, p):
		raise NotImplemented
