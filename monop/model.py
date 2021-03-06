from graph import Graph

import numpy as np
import math

def find_next(gn, ni, c):
	"Find next square from a given square which is a member of a given "
	"property group"

	for i in xrange(ni, ni + len(c.estates)):
		i %= len(c.estates)
		if c.estates[i].group < 0:
			continue
		g = c.groups[c.estates[i].group]
		if gn != g.name:
			continue
		return i
	return None

def go_out(state, v, p, is_double, c, rj, closure):
	"This is the guts of the build_model() function. It calculates the "
	"weight of a given outgoing edge in the markov model."

	i = state / c.JAIL_ROLLS
	d = state % c.JAIL_ROLLS
	e = c.estates[i]

	# if we're on go-to-jail, that means in-jail, the doubles counter
	# represents the amount of time spent in there.
	if i == c.tojail:
		# for rj we bump the stay-counter for every non doubles turn
		if rj and not is_double:
			ni = i
			nd = d + 1
			# if we tried c.JAIL_ROLLS times, then move to
			# just-visting
			if nd >= c.JAIL_ROLLS:
				ni = c.jail
				nd = 0
		elif not rj or is_double:
			# pay out at start of turn for lj strategy, or if
			# we rolled a double in rj then it's the same thing
			ni = c.jail + v
			nd = 0
	else:
		ni = i + v
		nd = is_double and d + 1 or 0

		# go to jail on 3rd double
		if nd >= c.JAIL_ROLLS:
			ni = c.tojail

		# If we land in jail, reset the doubles counter
		if ni == c.tojail:
			nd = 0

	ni %= len(c.estates)
	nxt = ni * c.JAIL_ROLLS + nd
	ne = c.estates[ni]

	# If the target has e.takecard then we need to figure out
	# cumulative probabilities for card moves.
	if ne.takecard:
		cardlist = c.cards[ne.takecard]
		for card in cardlist:
			if card.tojail:
				x = c.tojail
			elif card.advanceto >= 0:
				x = card.advanceto
			elif card.advance:
				x = ni + card.advance
			elif card.advancetonextof:
				gn = card.advancetonextof
				x = find_next(gn, ni, c)
			else:
				x = ni

			if x < 0:
				x = len(c.estates) - (abs(x) + 1)
			if x == c.tojail:
				y = 0
			else:
				y = nd

			np = (p * (1.0/len(cardlist)))
			x %= len(c.estates)
			nxt = x * c.JAIL_ROLLS + y
			#print np, c.estates[x], y
			closure(nxt, np)
		#print
	else:
		closure(nxt, p)

def build_model(dice, c, rj = True):
	"Build markov model given dice roll probabilities, "
	"a game configuration and whether to play the remain-in-jail or "
	"leave jail strategy. A graph of the markov model is returned"

	s = []
	for i, e in enumerate(c.estates):
		for d in xrange(c.JAIL_ROLLS):
			n = '%d_%d_'%(i, d) + e.name.replace(' ','_')
			s.append(n)
		#print ' o', i, e.name

	g = Graph(len(s))

	for ns, n in enumerate(s):
		out = {}
		def closure(nxt, p):
			assert(nxt < len(s))
			out[nxt] = out.get(nxt, 0.0) + p

		for v, Pr, Pd in dice.outcomes():
			if Pr:
				go_out(ns, v, Pr, False, c, rj, closure)
			if Pd:
				go_out(ns, v, Pd, True, c, rj, closure)

		#print n
		for v, k in sorted([(v,k) for (k,v) in out.items()]):
			#print v, s[k]
			g[ns, k] = v
		#print sum(out.values())
		#print

	#g.dump('markov-%s.dot'%(rj and 'rj' or 'lj'), s)
	return g

def do_eigenvector(A, k, d, epsilon=1e-5):
	"Eigenvector centrality"

	def mag_manhattan(a, b):
		return np.sum(a - b)
	def mag_euclidian(a, b):
		return np.linalg.norm(a - b)

	n = A.shape[0]
	r = np.mat([[1.0 for x in k]])
	t = np.mat([[1.0 for x in k]])
	isr = True
	cnt = 0
	mag = mag_euclidian
	#mag = mag_manhattan

	while True:
		if isr:
			np.dot(t, A, r[0])
			#t[0] *= d
			#t[0] += k
		else:
			np.dot(r, A, t[0])
			#r[0] *= d
			#r[0] += k
		cnt += 1

		if mag(r, t) <= epsilon:
			break

		isr = not isr

	if not isr:
		r = t

	print 'eigenvector found after %d iterations'%cnt
	ret = r[0] * (1.0 / r[0].sum())
	return ret.tolist()[0]

def pagerank(A, damping_factor = 0.85):
	"Pagerank is eigenvector centrality with a damping factor"
	n = A.shape[0]
	c = (1.0 - damping_factor) / float(n)
	k = [c for x in xrange(n)]
	return do_eigenvector(A, k, damping_factor)

def eigenvector(A):
	"Straght eigenvector centrality"
	n = A.shape[0]
	k = [0.0 for x in xrange(n)]
	return do_eigenvector(A, k, 1.0)

class Model(object):
	def __init__(self, c, d, rj = False):
		super(Model, self).__init__()
		self.c = c
		self.d = d
		self.rj = rj

		self.g = build_model(d, self.c, rj = self.rj)
		self.x = self.steady_state(self.g, self.c)
		(self.de, self.dg) = self.calc_tables(self.c, self.x)
		self.returns = self.calc_returns(self.c, self.de)
		self.amortized = self.calc_amortized(self.c, self.de)

	def steady_state(self, g, c):
		"Create a stochastic matrix from graph g and find the "
		"dominant eigenvector corresponding to eigenvalue 1.0"

		A = np.mat(np.zeros([len(g.U), len(g.U)]))
		for (x,y), v in g.items():
			A[x,y] = v

		#pr = pagerank(A)
		return eigenvector(A)

	def calc_tables(self, c, x):
		de = {}
		dg = {}
		for i,v in enumerate(x):
			idx = i / 3
			gdx = c.estates[idx].group
			if gdx < 0:
				gdx = c.estates[idx].name
			de[idx] = de.get(idx, 0.0) + v
			dg[gdx] = dg.get(gdx, 0.0) + v
		return (de, dg)

	def calc_returns(self, c, de):
		"Number of opponent rolls until break-even"
		returns = {}
		for k,v in de.items():
			e = c.estates[k]
			if e.group < 0:
				continue
			grp = c.groups[e.group]
			if grp.houseprice < 0:
				continue

			r0 = (grp.houseprice * 0 + e.price) / (v * e.rent0)
			r1 = (grp.houseprice * 0 + e.price) / (v * e.rent0 * 2)
			r2 = (grp.houseprice * 1 + e.price) / (v * e.rent1)
			r3 = (grp.houseprice * 2 + e.price) / (v * e.rent2)
			r4 = (grp.houseprice * 3 + e.price) / (v * e.rent3)
			r5 = (grp.houseprice * 4 + e.price) / (v * e.rent4)
			r6 = (grp.houseprice * 5 + e.price) / (v * e.rent5)

			t = (k, r0, r1, r2, r3, r4, r5, r6)
			returns[k] = t
		return returns

	def calc_amortized(self, c, de):
		"Amortised returns. Where development cost is irrelevant."
		ar = {}
		for k,v in de.items():
			e = c.estates[k]
			if e.group < 0:
				continue
			grp = c.groups[e.group]
			if grp.houseprice < 0:
				continue

			r0 = v * e.rent0
			r1 = v * e.rent0 * 2
			r2 = v * e.rent1
			r3 = v * e.rent2
			r4 = v * e.rent3
			r5 = v * e.rent4
			r6 = v * e.rent5

			t = (k, r0, r1, r2, r3, r4, r5, r6)
			ar[k] = t

		return ar

	def print_tables(self):
		print 'Steady-state probabilities for %s model'%(self.rj and \
						"RIJ" or "LJ")

		print 'Chance of landing on a given space'
		for v, k in sorted([(v,k) for (k,v) in self.de.items()],
					reverse=True):
			print '%.3f%% %s'%(v * 100.0, self.c.estates[k].name)
		print

		print 'Chance of landing on a member of a given group'
		for v, k in sorted([(v,k) for (k,v) in self.dg.items()],
					reverse=True):
			if isinstance(k, str):
				n = k
			else:
				n = self.c.groups[k].name
			print '%.3f%% %s'%(v * 100.0, n)
		print

		for i in xrange(1, 7):
			print 'Opponent turns to breakeven: %d houses'%(i-1)
			for (v, k) in sorted([(x[i], x[0]) \
					for x in self.returns.values()]):
				print '%.3f %s'%(v, self.c.estates[k].name)
			print

