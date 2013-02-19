from collections import namedtuple

GameType = namedtuple('GameType', ['gameid', 'name', 'gametype',
					'desc', 'canbejoined',
					'minplayers', 'maxplayers',
					'players', 'master'])
