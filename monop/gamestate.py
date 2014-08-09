class GameState(object):
	def __init__(self):
		super(GameState, self).__init__()
		self.abort()
		self.game_over()
	def game_over(self):
		self.groups = {}
		self.estates = {}
	def abort(self):
		self.game_over()
		self.players = {}
