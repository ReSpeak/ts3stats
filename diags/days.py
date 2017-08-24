from CreateTimeGraphs import *

def create_diag(dc):
	"""Time spent during all time (vip)"""
	# Initialize fields for users
	for u in dc.vip:
		u.dayTimes = [timedelta()] * dc.dayCount

	def f(u, con, slotStart, slotType, start, end):
		u.dayTimes[(slotStart.date() - dc.startDay).days] += end - start

	dc.fun_per_connected_slot(dc.vip, f)

	with openTempfile("days") as f:
		for u in dc.vip:
			dc.write_days(f, [t.total_seconds() for t in u.dayTimes], u.name)

	# Create the diagram
	diag = Diagram("days", "Time spent on TeamSpeak")
	diag.xlabel = "Date"
	diag.ylabel = "Connection time (in hours)"
	diag.appendText = """\
		set timefmt "%d.%m.%Y"
		set format x "%d.%m.%Y"
		set xdata time
		set xrange ["{0:%d.%m.%Y}":"{1:%d.%m.%Y}"]

		set style data lines
		set samples 1000
		""".format(dc.startDay, dc.endDay)
	diag.plots = ["index '{0}' using 1:2 title '{0}'" #smooth bezier
		.format(u.name) for u in dc.vip]

	diag.render(dc.diagramTemplate)
	dc.vipTab.addDiagram(diag)

	# Cumulative days
	with openTempfile("daysCumulative") as f:
		for u in dc.vip:
			dc.write_days(f, [t / timedelta(days = 1) for t in u.dayTimes], u.name, True)

	# Create the diagram
	diag2 = Diagram("daysCumulative")
	diag2.title = diag.title
	diag2.xlabel = diag.xlabel
	diag2.ylabel = "Connection time (in days)"
	diag2.appendText = diag.appendText
	diag2.plots = diag.plots
	diag2.render(dc.diagramTemplate)
	dc.vipTab.addDiagram(diag2)
