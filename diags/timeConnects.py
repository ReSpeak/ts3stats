from CreateTimeGraphs import *

def create_diag(dc):
	"""Connections per day"""
	# The amount of users online on a day
	days = [0] * dc.dayCount
	# The amount of joins and leaves on a day
	joins = [0] * dc.dayCount
	leaves = [0] * dc.dayCount
	timeouts = [0] * dc.dayCount

	for u in dc.users:
		u.onlineDays = [False] * dc.dayCount

	def f(u, con, slotStart, slotType, start, end):
		if (slotType & CONNECTION_START) != 0:
			joins[(slotStart.date() - dc.startDay).days] += 1
		u.onlineDays[(slotStart.date() - dc.startDay).days] = True
		if (slotType & CONNECTION_END) != 0:
			if con.timeout:
				timeouts[(slotStart.date() - dc.startDay).days] += 1
			else:
				leaves[(slotStart.date() - dc.startDay).days] += 1

	dc.fun_per_connected_slot(dc.users, f)

	for u in dc.users:
		for (i, d) in enumerate(u.onlineDays):
			if d:
				days[i] += 1

	descriptions = ["Online users", "Joins", "Timeouts"]
	values = [days, joins, timeouts]
	with openTempfile("connectstime") as f:
		for (desc, vals) in zip(descriptions, values):
			dc.write_days(f, vals, desc)

	# Create the diagram
	diag = Diagram("connectstime", "Connections per day", 1500, 600)
	diag.subtitle = "Fake timeouts: {0}".format(dc.fakeTimeouts)
	diag.xlabel = "Date"
	diag.ylabel = "Connections"
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
		.format(d) for d in descriptions]

	diag.render(dc.diagramTemplate)
	dc.generalTab.addDiagram(diag)

	descriptions = ["Leaves", "Joins", "Timeouts"]
	values = [leaves, joins, timeouts]
	with openTempfile("connectstimeCumulative") as f:
		for (desc, vals) in zip(descriptions, values):
			dc.write_days(f, vals, desc, True)

	# Create the cumulative diagram
	diag = Diagram("connectstimeCumulative", "Cumulative connections per day", 1500, 600)
	diag.xlabel = "Date"
	diag.ylabel = "Connections"
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
		.format(d) for d in descriptions]

	diag.render(dc.diagramTemplate)
	dc.generalTab.addDiagram(diag)
