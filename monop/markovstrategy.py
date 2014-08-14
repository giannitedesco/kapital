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

		net = self.player_net_worth(p)
		net = float(pc) * float(net) / 100.0
		self.msg('fixed price is %d, assets is %d\n'%(fixed, net))
		if net < fixed:
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

		# If development is uneven, add an option to even them out
		# by selling
		presell = {}
		sl = []
		sv = 0.0
		sc = 0
		while True:
			nh = sorted(map(lambda x:(x.houses -
						presell.get(x.estateid, 0),
					x), g), reverse = True)
			numhi, hi = nh[0]
			numlo, lo = nh[-1]

			if numlo == numhi:
				break
			sl.append((self.sell_house, hi.estateid))
			sc -= hi.sellhouseprice
			presell[hi.estateid] = presell.get(hi.estateid, 0) + 1
		if sl:
			for e in map(lambda x:self.s.estates[x],
					presell.keys()):
				before = m.amortized[e.estateid]\
					[2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + numlo]
				sv += after - before
			ret.append((sc, sv, sl))

		# Then add an option to sell n levels of houses starting
		# from an even base and ending with all properties mortgaged
		for nl in xrange(nh[0][0] - 1, -2, -1):
			things = []
			for j in xrange(nh[0][0] - 1, nl - 1, -1):
				for e in g:
					if j < 0:
						things.append((self.mortgage,
							e.estateid))
					else:
						things.append((self.sell_house,
							e.estateid))
			v = 0.0
			cost = 0
			for e in g:
				before = m.amortized[e.estateid]\
					[2 + e.houses]
				if nl < 0:
					after = 0.0
					cost += -e.sellhouseprice * nh[0][0]
					cost += -e.mortgageprice
				else:
					after = m.amortized[e.estateid][2 + nl]
					cost += -e.sellhouseprice \
						* (nh[0][0] - nl)
				diff = after - before
				v += diff
			ret.append((cost, v, sl + things))

		# Add an option to unmortgage them all, if any are mortgaged
		mc = 0
		mv = 0
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
		# by buying
		prebuy = {}
		bl = ml[:]
		bv = mv
		bc = 0
		while True:
			nh = sorted(map(lambda x:(x.houses +
						prebuy.get(x.estateid, 0),
					x), g))
			numlo, lo = nh[0]
			numhi, hi = nh[-1]

			if numlo == numhi:
				break
			bl.append((self.buy_house, lo.estateid))
			bc += lo.houseprice
			prebuy[lo.estateid] = prebuy.get(lo.estateid, 0) + 1
		if len(bl) > len(ml):
			for e in map(lambda x:self.s.estates[x], prebuy.keys()):
				before = m.amortized[e.estateid]\
					[2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + numhi]
				bv += after - before
			ret.append((bc, bv, bl))

		# Then add an option to buy n levels of houses starting
		# from an even base and ending with all hotels
		for nl in xrange(nh[-1][0] + 1, 6):
			things = []
			for j in xrange(nh[0][0], nl):
				for e in g:
					things.append((self.buy_house,
							e.estateid))
			v = 0.0
			for e in g:
				before = m.amortized[e.estateid]\
					[2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + nl]
				diff = after - before
				v += diff
			cost = g[0].houseprice * len(g) * \
					(nl - nh[0][0]) + bc
			ret.append((cost, v, bl + things))

		return ret

	def maximise_gains(self, b, max_weight):
		#self.msg('%d items to search\n'%\
		#	reduce(operator.mul, map(len, b), 1))

		# Brute force, we can't branch and bound here because of
		# negative costs and weights
		def recursive(cur, bleft, vsofar, capacity, max_weight, out):
			# hit bottom of search tree, evaluate
			if not bleft:
				# blown the limit
				if max_weight < 0:
					return

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

	def minimise_losses(self, b, min_weight):
		#self.msg('%d items to search\n'%\
		#	reduce(operator.mul, map(len, b), 1))

		# Brute force, we can't branch and bound here because of
		# negative costs and weights
		def recursive(cur, bleft, vsofar, capacity, min_weight, out):
			# hit bottom of search tree, evaluate
			if not bleft:
				# blown the limit
				(bestv, bestc, __) = out[0]
				if min_weight > capacity:
					return

				if vsofar > bestv:
					out[0] = (vsofar, min_weight, cur[:])
				return

			# evaluate all sub-trees
			for (w, v, _) in bleft[0]:
				cur.append(_)
				recursive(cur, bleft[1:], vsofar + v,
					capacity, min_weight + w, out)
				cur.pop()

		out = [(-float('inf'), 0, [])]
		recursive([], b, 0.0, -min_weight, 0, out)
		return out[0]

	def move_tree(self, p):
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
		return b

	def print_action(self, action, estateid):
		t = {'mortgage':'red',
			'unmortgage':'green',
			'buy_house':'blue',
			'sell_house':'purple',
		}
		a = action.__func__.func_name
		self.msg('%s'%a, [t.get(a, 'yellow')])
		self.msg(' %s\n'%self.s.estates[estateid].name)

	def print_actions(self, move):
		for action,estateid in move:
			self.print_action(action, estateid)

	def apply_move(self, move):
		for actions in move:
			for action,estateid in actions:
				self.print_action(action, estateid)
				action(estateid)

	def manage_estates(self, p):
		# First decide how much cash we're working with
		reserve = 200
		money = p.money - reserve
		if money < 0:
			return

		b = self.move_tree(p)

		# Print the options we have to chose from
		#for x in b:
		#	self.msg('bucket:\n', ['bold'])
		#	for (weight, value, actions) in x:
		#		self.msg('w=%d v=%.5f\n'%(weight, value))
		#		self.print_actions(actions)
		#		self.msg('\n')

		# Calculate optimal choices
		(returns, cost, l) = self.maximise_gains(b, money)
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
		self.apply_move(l)

	def raise_cash(self, p, target):
		b = self.move_tree(p)

		# Print the options we have to chose from
		#for x in b:
		#	self.msg('bucket:\n', ['bold'])
		#	for (weight, value, actions) in x:
		#		self.msg('w=%d v=%.5f\n'%(weight, value))
		#		self.print_actions(actions)
		#		self.msg('\n')

		self.msg('Raising: %u bucks\n'%target, ['bold'])
		(losses, raised, l) = self.minimise_losses(b, target)
		raised = -raised
		if raised < target:
			# should never get here
			self.msg('only raised %d bucks\n'%raised,
				['bold','red'])
			return False

		self.apply_move(l)
		self.msg('raised %d bucks\n'%raised, ['bold','dark green'])
		return True


gobject.type_register(MarkovStrategy)
