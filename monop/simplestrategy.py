from strategy import Strategy
import gobject

class SimpleStrategy(Strategy):
	def __init__(self):
		super(SimpleStrategy, self).__init__()

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

	def manage_estates(self, p):
		money = p.money
		hand = self.hand(p)

		# unmortgage properties
		reserve = 200
		for e in hand:
			if not e.mortgaged:
				continue

			if money < e.unmortgageprice + reserve:
				continue

			self.unmortgage(e.estateid)
			money -= e.unmortgageprice

		# buy houses
		(monopolies, misc) = self.split_hand(hand)
		for m in monopolies:
			tc = sum(map(lambda x:x.houseprice, m))
			if money < reserve + tc:
				continue
			if m[0].houses < 5:
				self.msg('monopoly: buying a level on %s for %d\n'%\
					(self.s.groups[m[0].group].name, tc),
					['bold', 'dark blue'])
			for e in m:
				if e.houses >= 5:
					continue
				self.msg(' - %r\n'%e, ['bold', 'dark blue'])
				self.buy_house(e.estateid)
				e.houses += 1
			money -= tc

gobject.type_register(SimpleStrategy)
