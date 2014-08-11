class Universe(frozenset):
	def __new__(cls, card):
		return super(Universe, cls).__new__(cls, xrange(card))

class Graph(dict):
	def __init__(self, init):
		super(Graph, self).__init__()
		if isinstance(init, Universe):
			U = init
		else:
			U = Universe(int(init))
		self.U = U

	def __getitem__(self, (x,y)):
		assert(x < len(self.U))
		assert(y < len(self.U))
		try:
			return super(Graph, self).__getitem__((x,y))
		except KeyError:
			return 0.0

	def __setitem__(self, (x,y), v):
		if not isinstance(v, float):
			raise TypeError
		super(Graph, self).__setitem__((x,y), v)
	
	def __str__(self):
		rows = []
		for i in xrange(len(self.U)):
			r = ' '.join(map(lambda x:'%.3f'%self[i,x],
					xrange(len(self.U))))
			rows.append(r)
		return '\n'.join(rows)

	def image(self, n):
		assert(n < len(self.U))
		ret = []
		for i in xrange(len(self.U)):
			if self[n,i]:
				ret.append(i)
		return frozenset(ret)

	def preimage(self, n):
		assert(n < len(self.U))
		ret = []
		for i in xrange(len(self.U)):
			if self[i,n]:
				ret.append(i)
		return frozenset(ret)

	def dump(self, fn, names = None):
		def q(s):
			return '\"%s\"'%s
		f = open(fn, 'w')
		f.write('digraph %s {\n'%q('Monopoly Markov Model'))
		f.write('\tgraph[rankdir=LR]\n')
		f.write('\tnode [shape = rectangle];\n')
		f.write('\n')
		def add_node(n, **kwargs):
			n = q(n)
			a = ' '.join(map(lambda (k,v):'%s=%s'%(k, q(v)),
					kwargs.items()))
			f.write('%s [%s];\n'%(n,a))
		def add_edge(pre, post, label):
			pre = q(pre)
			post = q(post)
			label = q(label)
			f.write('%s -> %s [label=%s];\n'%(pre, post, label))

		if names is None:
			names = map(lambda x:'%d'%x, sorted(self.U))
		for v in self.U:
			add_node(v, label=names[v])

		for (pre, post), val in self.items():
			add_edge(pre, post, label='%g'%val)

		f.write('}\n')
		f.close()
