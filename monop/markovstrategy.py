from strategy import Strategy
from dice import Dice
from model import Model
from functools import reduce
import operator
import gobject

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
			self.unmortgge(e.estateid)
			raised += e.mortgageprice

		if raised >= target:
			return raised

		# now to sell houses, sell entire rows at once
		# just to keep it simple
		for g in monopolies:
			if True in map(lambda x:x.mortgaged,g):
				continue
			if raised >= target:
				break
			for e in g:
				if e.houses <= 0:
					continue
				self.sell_house(e.estateid)
				# FIXME
				e.houses -= 1
				raised += e.sellhouseprice

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
			self.msg('not sure what to do\n')
			due = 100
		self.raise_cash(p, due)

	def handle_purchase(self, p):
		e = self.s.estates[p.location]
		self.msg('price is %d, i gots %d\n'%(e.price, p.money))
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

	def management_choices(self, m, g):
		nh = sorted(map(lambda x:x.houses, g))
		if g[0].houseprice <= 0:
			return

		# FIXME: assert even development
		assert(nh[0], nh[-1])

		mc = 0
		ml = []
		for e in filter(lambda x:x.mortgaged, g):
			ml.append((self.unmortgage, e.estateid))
			mc += e.unmortgageprice

		ret = []
		for nl in xrange(nh[0], 6):
			things = []
			for j in xrange(1, nl + 1):
				for e in g:
					things.append((self.buy_house,
							e.estateid))
			for e in g:
				before = m.amortized[e.estateid][2 + e.houses - int(e.mortgaged)]
				after = m.amortized[e.estateid][2 + nl]
				diff = after - before
			cost = g[0].houseprice * len(g) * nl + mc
			if cost == 0.0:
				cost = 1.0
			ret.append(((cost, diff/cost), ml + things))
		return ret

	def optimal_moves(self, b, max_weight):
		def recursive(cur, bleft, vsofar, max_weight, out):
			if max_weight < 0:
				return
			if not bleft:
				(bestv, _) = out[0]
				if vsofar > bestv:
					out[0] = (vsofar, cur[:])
				return
			for ((w, v), _) in bleft[0]:
				cur.append(_)
				recursive(cur, bleft[1:], vsofar + v,
					max_weight - w, out)
				cur.pop()
			return
		out = [(0.0, [])]
		recursive([], b, 0.0, max_weight, out)
		return out[0]

	def manage_estates(self, p):
		reserve = 200
		money = p.money - reserve
		self.msg('Manage estates: %u cash - reserve %u = %u\n'%(
			p.money, reserve, money))

		hand = self.hand(p)
		(monopolies, misc) = self.split_hand(hand)

		if True:
			m = self.m_lj
		else:
			m = self.m_rj

		b = []
		for e in misc:
			try:
				v = m.amortized[e.estateid][1]
			except:
				# FIXME: railroads and utilities
				v = m.de[e.estateid] * 50

			if e.mortgaged:
				bucket = ((e.mortgageprice, v),
						[(self.unmortgage, e.estateid)])
			else:
				bucket = ((-e.mortgageprice, -v),
						[(self.mortgage, e.estateid)])

			#b.append([((0, 0.0), []), bucket])

		for g in monopolies:
			x = self.management_choices(m, g)
			if x is not None:
				b.append(x)

		#for x in b:
		#	self.msg('bucket:\n', ['bold'])
		#	for ((weight, value), actions) in x:
		#		self.msg('w=%d v=%.5f\n'%(weight, value))
		#		for action,estateid in actions:
		#			a = action.__func__.func_name
		#			if a == 'mortgage':
		#				tag = 'red'
		#			elif a == 'unmortgage':
		#				tag = 'green'
		#			elif a == 'buy_house':
		#				tag = 'cyan'
		#			elif a == 'sell_house':
		#				tag = 'magenta'
		#			else:
		#				tag = 'yellow'
		#			self.msg('%s'%a, [tag])
		#			self.msg(' %s\n'%self.s.estates[estateid].name)
		#		self.msg('\n')

		(returns, l) = self.optimal_moves(b, money)
		self.msg('optimal (expected return %.5f:\n'%returns, ['bold'])
		for actions in l:
			for action,estateid in actions:
				a = action.__func__.func_name
				if a == 'mortgage':
					tag = 'red'
				elif a == 'unmortgage':
					tag = 'green'
				elif a == 'buy_house':
					tag = 'cyan'
				elif a == 'sell_house':
					tag = 'magenta'
				else:
					tag = 'yellow'
				self.msg('%s'%a, [tag])
				self.msg(' %s\n'%self.s.estates[estateid].name)
				action(estateid)

gobject.type_register(MarkovStrategy)
