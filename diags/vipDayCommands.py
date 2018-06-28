from CreateTimeGraphs import *

def create_diag(dc):
	"""Bot commands during a day (vip)"""
	if not botStats:
		return
	# The vip average for each slot on a day
	commands = [0] * slotsPerDay
	botUsers = []

	for u in dc.vip:
		if len(u.botPlays) == 0 and len(u.botCommands) == 0:
			continue

		u.commands = [0] * slotsPerDay
		botUsers.append(u)
		for c in u.botPlays:
			commands[to_slot_index(c[0])] += 1
			u.commands[to_slot_index(c[0])] += 1
		for c in u.botCommands:
			commands[to_slot_index(c[0])] += 1
			u.commands[to_slot_index(c[0])] += 1

	with openTempfile("vipdaycommands") as f:
		for u in botUsers:
			dc.write_slots_per_day(f, u.commands, u.name)
		dc.write_slots_per_day(f, [c / len(botUsers) for c in commands], "Average")

	# Create the diagram
	diag = Diagram("vipdaycommands", "Commands during a day (vip)", 1500, 600)
	diag.subtitle = "Vip bot users: {0}/{1}".format(len(botUsers), len(dc.vip))
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
		for t in [u.name for u in botUsers] + ["Average"]]

	diag.render(dc.diagramTemplate)
	dc.botTab.addDiagram(diag)
