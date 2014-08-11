class Dice(object):
	def __init__(self):
		super(Dice, self).__init__()
		r = [0 for x in xrange(6 * 2 + 2)] # 0 and 1 not possible
		d = [0 for x in xrange(6 * 2 + 2)]
		for i in xrange(1,7):
			for j in xrange(1,7):
				if i == j:
					d[i + j] += 1
				else:
					r[i + j] += 1
		self.__out = []
		space = float(6 * 6)
		for score, (rr, dd) in enumerate(zip(r, d)):
			if not rr and not dd:
				continue
			self.__out.append((score, rr/space, dd/space))
		#sum([sum((x, y)) for (a,x,y) in self.__out]) == 1.0

	# return list of tuples of (score, Pr, Pd) representing
	# the set of all possible dice outcomes where:
	#  - score = sum of dice face values
	#  - Pr = probability of rolling this NOT as doubles
	#  - Pd = probability of rolling this as doubles
	def outcomes(self):
		return self.__out
