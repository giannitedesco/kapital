from tcpsock import TCPSock
from socket import error as SockError
from errno import EINPROGRESS, EAGAIN

class LineSock(TCPSock):
	def __init__(self):
		TCPSock.__init__(self)
		self.__buf = ''

	def _read(self):
		try:
			new = self._sock.recv(4096)
		except SockError, e:
			if e.errno == EINPROGRESS or e.errno == EAGAIN:
				return
			else:
				self.emit('error', 'recv', e.strerror)
				return

		if new == '':
			self.emit('disconnected')
			return

		self.__buf += new
		while '\n' in self.__buf:
			(msg, rest) = self.__buf.split('\n', 1)
			msg = msg.rstrip('\r')
			self.emit('data-in', msg)
			self.__buf = rest
