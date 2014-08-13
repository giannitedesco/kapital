from strategy import Strategy
from dice import Dice
from model import Model
from functools import reduce
import operator
import gobject
from math import factorial

class MarkovStrategy(Strategy):
	def __init__(self, conf):
		super(MarkovStrategy, self).__init__()
		d = Dice()
		self.m_rj = Model(conf, d, rj = True)
		self.m_lj = Model(conf, d, rj = False)

	def do_raise_cash(self, target, hand):
		raised = 0

		(monopolies, crap) = self.split_hand(hand)

		# first try mortgage properties that are not
		# part of monopolies
		for e in crap:
			if raised >= target or e.mortgaged or e.houses > 0:
				continue
			self.mortgage(e.estateid)
			raised += e.mortgageprice

		if raised >= target:
			return raised

		# now try mortgage undeveloped monopolies
		monoplist = sum(monopolies, [])
		for e in monoplist:
			if raised >= target or e.mortgaged or e.houses > 0:
				continue
			self.unmortgage(e.estateid)
			raised += e.mortgageprice

		if raised >= target:
			return raised

		# now to sell houses, sell entire rows at once
		# just to keep it simple
		while raised < target:
			this_time = 0
			for g in monopolies:
				if False not in map(lambda x:x.mortgaged,g):
					continue
				if raised >= target:
					break
				for num,e in sorted(map(lambda x:(x.houses,x),g),
							reverse=True):
					if e.houses <= 0:
						continue
					self.sell_house(e.estateid)
					# FIXME
					e.houses -= 1
					this_time += e.sellhouseprice
			if not this_time:
				break
			raised += this_time

		# shouldn't really be possible, we're bust
		return raised

	def raise_cash(self, p, target):
		hand = self.hand(p)
		for e in hand:
			self.msg('I own: [%d]: %s\n'%(e.estateid, e.name),
				[e.mortgaged and 'red' or 'dark green'])
		self.msg('must raise %d bucks!\n'%target)

		raised = self.do_raise_cash(target, hand)
		if raised < target:
			# should never get here
			self.msg('only raised %d bucks\n'%raised,
				['bold','red'])
			return False

		self.msg('raised %d bucks\n'%raised, ['bold','dark green'])
		return True

	def handle_debt(self, p):
		self.msg('handle debts\n')
		e = self.s.estates[p.location]
		due = self.due(p, e)
		if due <= 0:
			self.msg('not sure what to do\n', ['bold', 'red'])
			due = 100
		self.raise_cash(p, due)

	def handle_purchase(self, p):
		e = self.s.estates[p.location]
		self.msg('price of %s is %d, i gots %d\n'%(e.name,
							e.price,
							p.money))
		if e.price > p.money:
			can_afford = self.raise_cash(p, e.price - p.money)
		else:
			can_afford = True

		if can_afford:
			self.msg('BUYING IT, THEY HATIN\n', ['dark green'])
			return True
		else:
			self.msg('CANNOT AFFORD, AUCTION\n', ['red'])
			return False

	def remain_in_jail(self, i):
		# decide whether to pay, use card, or what
		if i.money < 50:
			self.raise_cash(i, 50 - i.money)
		self.msg('BUYING OUT OF JAIL\n', ['red'])
		return False

	def pay_asset_tax(self, p):
		self.msg('got %d bucks\n'%p.money)

		e = self.s.estates[p.location]
		pc = e.taxpercentage and e.taxpercentage or 10
		fixed = e.tax and e.tax or 200

		money = p.money
		for e in self.hand(p):
			self.msg('I own: %s (%d + %d)\n'%(e.name,
				e.mortgageprice, e.houses * e.sellhouseprice),
				[e.mortgaged and 'red' or 'dark green'])
			if not e.mortgaged:
				money += e.mortgageprice
				money += e.houses * e.sellhouseprice
		money = float(pc) * float(money) / 100.0
		self.msg('fixed price is %d, assets is %d\n'%(fixed, money))
		if money < fixed:
			self.msg('PAYING PERCENTAGE\n', ['dark green'])
			return True
		else:
			self.msg('PAYING FIXED\n', ['red'])
			return False

	def misc_options(self, m, e):
		try:
			v = m.amortized[e.estateid][1]
		except:
			# FIXME: railroads and utilities
			v = m.de[e.estateid] * 50

		if e.mortgaged:
			bucket = (e.unmortgageprice, v,
					[(self.unmortgage, e.estateid)])
		else:
			bucket = (-e.mortgageprice, -v,
					[(self.mortgage, e.estateid)])

		return [(0, 0.0, []), bucket]

	def monopoly_options(self, m, g):
		# exclude utilities and railroads
		if g[0].houseprice <= 0:
			# FIXME: should at least unmortgage them
			return

		# Start with a "do nothing" option
		ret = [(0,0,[])]

		# Add an option to unmortgage them all, if any are mortgaged
		mc = 0
		mv = 0.0
		ml = []
		for e in filter(lambda x:x.mortgaged, g):
			ml.append((self.unmortgage, e.estateid))
			mc += e.unmortgageprice
			before = m.amortized[e.estateid][0]
			after = m.amortized[e.estateid][2]
			mv += after - before
		if ml:
			ret.append((mc, mv, ml))

		# If development is uneven, add an option to even them out
		prebuy = {}
		el = ml[:]
		ev = mv
		ec = 0.0
		while True:
			nh = sorted(map(lambda x:(x.houses +
						prebuy.get(x.estateid, 0),
					x), g))
			numlo, lo = nh[0]
			numhi, hi = nh[-1]

			if numlo == numhi:
				break
			el.append((self.buy_house, lo.estateid))
			ec += lo.houseprice
			prebuy[lo.estateid] = prebuy.get(lo.estateid, 0) + 1
		if len(el) > len(ml):
			for e in map(lambda x:self.s.estates[x], prebuy.keys()):
				before = m.amortized[e.estateid]\
					[2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + numhi]
				ev += after - before
			ret.append((ec, ev, el))

		# Then add an option to buy n levels of houses starting
		# from an even base and ending with all hotels
		for nl in xrange(nh[0][0] + 1, 6):
			things = []
			for j in xrange(nh[0][0], nl):
				for e in g:
					things.append((self.buy_house,
							e.estateid))
			for e in g:
				before = m.amortized[e.estateid]\
					[2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + nl]
				diff = after - before
			cost = g[0].houseprice * len(g) * \
					(nl - nh[0][0]) + ec
			ret.append((cost, diff, el + things))
		return ret

	def optimal_moves(self, b, max_weight):
		# Brute force, we can't branch and bound here because of
		# negative costs and weights
		def recursive(cur, bleft, vsofar, capacity, max_weight, out):
			# blown the limit
			if max_weight < 0:
				return

			# hit bottom of search tree, evaluate
			if not bleft:
				this_cost = capacity - max_weight
				(bestv, bestc, __) = out[0]
				if vsofar > bestv:
					out[0] = (vsofar, this_cost, cur[:])
				return

			# evaluate all sub-trees
			for (w, v, _) in bleft[0]:
				cur.append(_)
				recursive(cur, bleft[1:], vsofar + v,
					capacity, max_weight - w, out)
				cur.pop()

		out = [(0.0, max_weight, [])]
		recursive([], b, 0.0, max_weight, max_weight, out)
		return out[0]

	def manage_estates(self, p):
		# First decide how much cash we're working with
		reserve = 200
		money = p.money - reserve
		if money < 0:
			return

		# Decide which model to use for opponent rolls
		if True:
			m = self.m_lj
		else:
			m = self.m_rj

		# Split the hand in to monopolies and misc
		hand = self.hand(p)
		(monopolies, misc) = self.split_hand(hand)

		# Construct an array of options for each misc estate, and
		# for each monopoly as a whole
		b = []
		for e in misc:
			x = self.misc_options(m, e)
			if x is not None:
				b.append(x)
		for g in monopolies:
			x = self.monopoly_options(m, g)
			if x is not None:
				b.append(x)

		t = {'mortgage':'red',
			'unmortgage':'green',
			'buy_house':'blue',
			'sell_house':'purple',
		}

		# Print the options we have to chose from
		#for x in b:
		#	self.msg('bucket:\n', ['bold'])
		#	for ((weight, value), actions) in x:
		#		self.msg('w=%d v=%.5f\n'%(weight, value))
		#		for action,estateid in actions:
		#			a = action.__func__.func_name
		#			self.msg('%s'%a, [t.get(a, 'yellow')])
		#			self.msg(' %s\n'%self.s.estates[estateid].name)
		#		self.msg('\n')

		# Calculate optimal choices
		(returns, cost, l) = self.optimal_moves(b, money)
		if returns < 0:
			return

		# Don't clutter up the output if we're not doing anything
		shout = False
		for actions in l:
			for action,estateid in actions:
				shout = True
				break
		if shout:
			self.msg('Manage estates: %u cash - reserve %u = %u\n'%(
				p.money, reserve, money), ['bold'])
			self.msg('Optimal: outlay %u, expected return %.5f\n'%(
					cost, returns),
					['bold'])
			self.msg('%.3f opponent rolls to recoup\n'%(
				cost/returns), ['bold'])

		# Implement the actions
		for actions in l:
			for action,estateid in actions:
				a = action.__func__.func_name
				self.msg('%s'%a, [t.get(a, 'yellow')])
				self.msg(' %s\n'%self.s.estates[estateid].name)
				action(estateid)

gobject.type_register(MarkovStrategy)
