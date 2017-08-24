from CreateTimeGraphs import *

def create_diag(dc):
	"""Commands per day"""
	if dc.startDayBot == None:
		return
	botUsers = []

	for u in dc.vip:
		if len(u.botPlays) == 0 and len(u.botCommands) == 0:
			continue

		u.commands = [0] * dc.dayCountBot
		botUsers.append(u)
		for c in u.botPlays:
			if type(c[0]) is datetime:
				u.commands[(c[0].date() - dc.startDayBot).days] += 1
		for c in u.botCommands:
			if type(c[0]) is datetime:
				u.commands[(c[0].date() - dc.startDayBot).days] += 1

	with openTempfile("vipcommandstime") as f:
		for u in botUsers:
			dc.write_days(f, u.commands, u.name, start = dc.startDayBot)

	# Create the diagram
	diag = Diagram("vipcommandstime", "Commands per day (vip)", 1500, 600)
	diag.xlabel = "Date"
	diag.ylabel = "Commands"
	diag.appendText = """\
		set timefmt "%d.%m.%Y"
		set format x "%d.%m.%Y"
		set xdata time
		set xrange ["{0:%d.%m.%Y}":"{1:%d.%m.%Y}"]

		set style data lines
		set key autotitle columnhead
		set samples 100
		""".format(dc.startDayBot, dc.endDayBot)
	diag.plots = ["index '{0}' using 1:2 title '{0}'"
		.format(u.name) for u in botUsers]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)

	with openTempfile("vipcommandstimeCumulative") as f:
		for u in botUsers:
			dc.write_days(f, u.commands, u.name, True, start = dc.startDayBot)

	# Create the cumulative diagram
	diag = Diagram("vipcommandstimeCumulative", "Cumulative commands per day (vip)", 1500, 600)
	diag.xlabel = "Date"
	diag.ylabel = "Commands"
	diag.appendText = """\
		set timefmt "%d.%m.%Y"
		set format x "%d.%m.%Y"
		set xdata time
		set xrange ["{0:%d.%m.%Y}":"{1:%d.%m.%Y}"]

		set style data lines
		set key autotitle columnhead
		set samples 100
		""".format(dc.startDayBot, dc.endDayBot)
	diag.plots = ["index '{0}' using 1:2 title '{0}'"
		.format(u.name) for u in botUsers]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)
