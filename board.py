#!/usr/bin/python

import gobject, gtk, cairo
import math

class Board(gtk.DrawingArea):
	def hex2float(self, *args):
		return map(lambda x:x * (1.0 / 0x100), args)

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

		# draw inline
		x = (s / 7.25)
		y = s - (2 * x)
		
		boxes = []
		for i in xrange(0, 8):
			mins = (x + (i * (y / 8)), y + x)
			maxs = (x + ((i + 1) * (y / 8)),  s)
			allfour = (i == 0)
			boxes.append((mins, maxs, allfour))
		for i in xrange(0, 8):
			mins = (x, x + (i * (y / 8)))
			maxs = (0, x + ((i + 1) * (y / 8)))
			allfour = (i == 0)
			boxes.append((mins, maxs, allfour))
		for i in xrange(0, 8):
			mins = (x + (i * (y / 8)), x)
			maxs = (x + ((i + 1) * (y / 8)), 0)
			allfour = (i == 7)
			boxes.append((mins, maxs, allfour))
		for i in xrange(0, 8):
			mins = (x + y, x + (i * (y / 8)))
			maxs = (s, x + ((i + 1) * (y / 8)))
			allfour = (i == 7)
			boxes.append((mins, maxs, allfour))

#		cols = [ \
#			(0, 0, 0),
#			(0, 0, 1.0),
#			(0, 1.0, 0),
#			(1.0, 0, 0)
#			]
#		i = 0
		
		cr.set_source_rgb(0, 0, 0)
		for (mins,maxs,allfour) in boxes:
#			if i % 8 == 0:
#				cr.set_source_rgb(*cols.pop())
#			i += 1

			d = (abs(maxs[0] - mins[0]),
				abs(maxs[1] - mins[1]))
			sz = (min(d), max(d))

			if d[0] < d[1]:
				if mins[1] < maxs[1]:
					t = mins
					r = 0
				else:
					t = (maxs[0], mins[1])
					r = math.pi
			else:
				if mins[0] < maxs[0]:
					t = (mins[0], maxs[1])
					r = math.pi * 1.5
				else:
					t = mins
					r = math.pi / 2

			m = cr.get_matrix()
			cr.translate(t[0], t[1])
			cr.rotate(r)
			if allfour:
				cr.move_to(0, sz[1])
				cr.line_to(0, 0)
			else:
				cr.move_to(0, 0)
			cr.line_to(sz[0], 0)
			cr.line_to(sz[0], sz[1])
			cr.stroke()
			cr.set_matrix(m)


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

	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.connect('expose-event', self.expose)
