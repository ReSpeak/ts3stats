from CreateTimeGraphs import *

def create_diag(dc):
	"""Vip connections per day"""
	for u in dc.vip:
		u.joins = [0] * dc.dayCount
		u.leaves = [0] * dc.dayCount
		u.timeouts = [0] * dc.dayCount
		for c in u.connections:
			u.joins[(c.start.date() - dc.startDay).days] += 1
			if c.timeout:
				u.timeouts[(c.end.date() - dc.startDay).days] += 1
			else:
				u.leaves[(c.end.date() - dc.startDay).days] += 1

	with openTempfile("vipconnects") as f:
		for u in dc.vip:
			dc.write_days(f, u.joins, u.name, True)

	# Create the diagram
	diag = Diagram("vipconnects", "Cumulative joins per day", 1500, 600)
	diag.xlabel = "Date"
	diag.ylabel = "Joins"
	diag.appendText = """\
		set timefmt "%d.%m.%Y"
		set format x "%d.%m.%Y"
		set xdata time
		set xrange ["{0:%d.%m.%Y}":"{1:%d.%m.%Y}"]

		set style data lines
		set key autotitle columnhead
		set samples 100
		""".format(dc.startDay, dc.endDay)
	diag.plots = ["index '{0}' using 1:2 title '{0}'"
		.format(u.name) for u in dc.vip]

	diag.render(dc.diagramTemplate)
	dc.vipTab.addDiagram(diag)
