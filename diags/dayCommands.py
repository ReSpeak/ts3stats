from CreateTimeGraphs import *

def create_diag(dc):
	"""Bot commands during a day"""
	if not botStats:
		return
	# The ... for each slot on a day
	plays = [0] * slotsPerDay
	commands = [0] * slotsPerDay
	botUsers = 0

	for u in dc.users:
		if len(u.botPlays) == 0 and len(u.botCommands) == 0:
			continue

		botUsers += 1
		for c in u.botPlays:
			plays[to_slot_index(c[0])] += 1
		for c in u.botCommands:
			commands[to_slot_index(c[0])] += 1

	with openTempfile("daycommands") as f:
		dc.write_slots_per_day(f, plays, "Plays")
		dc.write_slots_per_day(f, commands, "Commands")

	# Create the diagram
	diag = Diagram("daycommands", "Commands during a day", 1500, 600)
	diag.subtitle = "Bot users: {0}".format(botUsers)
	diag.xlabel = "Daytime"
	diag.ylabel = "Commands"
	diag.legend = "at graph 0.2, 0.95"
	diag.appendText = """\
		set timefmt "%H:%M"
		set format x "%H:%M"
		set xdata time
		set xrange ["00:00":"24:00"]

		set style data lines
		set key autotitle columnhead
		set samples 1000
		"""
	diag.plots = ["index '{0}' using 1:2 title '{0}'".format(t)
		for t in ["Plays", "Commands"]]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)
