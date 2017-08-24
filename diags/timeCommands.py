from CreateTimeGraphs import *

def create_diag(dc):
	"""Commands per day"""
	if dc.startDayBot == None:
		return
	# The amount of commands on a day
	commands = [0] * dc.dayCountBot
	plays = [0] * dc.dayCountBot
	commandCount = 0
	playCount = 0

	for u in dc.users:
		for c in u.botPlays:
			if type(c[0]) is datetime:
				plays[(c[0].date() - dc.startDayBot).days] += 1
				playCount += 1
		for c in u.botCommands:
			if type(c[0]) is datetime:
				commands[(c[0].date() - dc.startDayBot).days] += 1
				commandCount += 1

	descriptions = ["Plays", "Commands"]
	values = [plays, commands]
	with openTempfile("commandstime") as f:
		for (desc, vals) in zip(descriptions, values):
			dc.write_days(f, vals, desc, start = dc.startDayBot)

	# Create the diagram
	diag = Diagram("commandstime", "Commands per day", 1500, 600)
	diag.subtitle = "Total: {} commands, {} plays".format(commandCount, playCount)
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
		.format(d) for d in descriptions]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)

	descriptions = ["Plays", "Commands"]
	values = [plays, commands]
	with openTempfile("commandstimeCumulative") as f:
		for (desc, vals) in zip(descriptions, values):
			dc.write_days(f, vals, desc, True, start = dc.startDayBot)

	# Create the cumulative diagram
	diag = Diagram("commandstimeCumulative", "Cumulative commands per day", 1500, 600)
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
		.format(d) for d in descriptions]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)
