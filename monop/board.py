import gobject, gtk, cairo
from collections import namedtuple
import math

Box = namedtuple('Box', ['boxid', 't', 'r', 'sz', 'border'])

class Board(gtk.DrawingArea):
	def hex2float(self, *args):
		return map(lambda x:x * (1.0 / 0x100), args)
	
	def gen_boxes(self):
		s = 1.0
		x = (s / 7.25)
		y = s - (2 * x)
		
		boxes = []
		boxid = 0

		i = 0
		boxes.append(((s - x, s - x), (s, s), 0, boxid))
		boxid += 1
		for i in xrange(8, -1, -1):
			mins = (x + (i * (y / 9)), y + x)
			maxs = (x + ((i + 1) * (y / 9)),  s)
			border = (i == 0) and 4 or 3
			boxes.append((mins, maxs, border, boxid))
			boxid += 1
		boxes.append(((0, s - x), (x, s), 0, boxid))
		boxid += 1
		for i in xrange(8, -1, -1):
			mins = (x, x + (i * (y / 9)))
			maxs = (0, x + ((i + 1) * (y / 9)))
			border = (i == 0) and 4 or 3
			boxes.append((mins, maxs, border, boxid))
			boxid += 1
		boxes.append(((0, 0), (x, x), 0, boxid))
		boxid += 1
		for i in xrange(0, 9):
			mins = (x + (i * (y / 9)), x)
			maxs = (x + ((i + 1) * (y / 9)), 0)
			border = (i == 8) and 4 or 3
			boxes.append((mins, maxs, border, boxid))
			boxid += 1
		boxes.append(((s - x, x), (s, 0), 0, boxid))
		boxid += 1
		for i in xrange(0, 9):
			mins = (x + y, x + (i * (y / 9)))
			maxs = (s, x + ((i + 1) * (y / 9)))
			border = (i == 8) and 4 or 3
			boxes.append((mins, maxs, border, boxid))
			boxid += 1

		self.boxes = []
		for (mins,maxs,border,boxid) in boxes:
			d = (abs(maxs[0] - mins[0]),
				abs(maxs[1] - mins[1]))
			sz = (min(d), max(d))

			if d[0] <= d[1]:
				if mins[1] <= maxs[1]:
					t = mins
					r = 0
				else:
					t = (maxs[0], mins[1])
					r = math.pi
			else:
				if mins[0] <= maxs[0]:
					t = (mins[0], maxs[1])
					r = math.pi * 1.5
				else:
					t = mins
					r = math.pi / 2
			# nasty hack
			if boxid == 30:
				r = 0
			self.boxes.append(Box(boxid, t, r, sz, border))



	def board(self, cr, s):
		# fill background
		cr.set_source_rgb(*self.hex2float(0xbf, 0xf7, 0xd0))
		cr.rectangle(0, 0, s, s)
		cr.fill()

		cr.set_line_cap(cairo.LINE_CAP_ROUND)
		cr.set_line_join(cairo.LINE_JOIN_ROUND)
		cr.set_line_width(1)

		cr.set_source_rgb(0, 0, 0)

		# draw outline
		cr.rectangle(0, 0, s, s)
		cr.stroke()

		# draw boxes
		for box in self.boxes:
			sz = map(lambda x:x*s, box.sz)
			t = map(lambda x:x*s, box.t)
			cr.save()
			cr.translate(t[0], t[1])
			cr.rotate(box.r)
			if self.draw_box is not None:
				self.draw_box(cr, sz, box.boxid)
			cr.set_source_rgb(0, 0, 0)
			if box.border:
				if box.border == 4:
					cr.move_to(0, sz[1])
					cr.line_to(0, 0)
				else:
					cr.move_to(0, 0)
				cr.line_to(sz[0], 0)
				cr.line_to(sz[0], sz[1])
				cr.stroke()
			cr.restore()


	def draw(self, cr, w, h):
		w -= 10
		h -= 10

		x = min(w, h)
		cr.translate(5 + ((w - x)/2), 5 + ((h - x)/2))
		self.board(cr, x)

	def expose(self, _, event):
		cr = self.window.cairo_create()
		cr.rectangle(event.area.x, event.area.y,
				event.area.width, event.area.height)
		cr.clip()
		a = self.get_allocation()
		self.draw(cr, a.width, a.height)

	def redraw(self):
		if self.window is not None:
			x = self.window.get_geometry()
			self.window.invalidate_rect((0, 0, x[2], x[3]), True)

	def __init__(self, draw_box = None):
		gtk.DrawingArea.__init__(self)
		self.gen_boxes()
		self.draw_box = draw_box
		self.connect('expose-event', self.expose)
