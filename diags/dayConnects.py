from CreateTimeGraphs import *

def create_diag(dc):
	"""Connections during a day"""
	# Global connections
	# The ... for each slot on a day
	joins = [0] * slotsPerDay
	leaves = [0] * slotsPerDay
	timeouts = [0] * slotsPerDay

	for u in dc.users:
		for c in u.connections:
			joins[to_slot_index(c.start)] += 1
			if c.timeout:
				timeouts[to_slot_index(c.end)] += 1
			else:
				leaves[to_slot_index(c.end)] += 1

	with openTempfile("dayconnects") as f:
		dc.write_slots_per_day(f, joins, "Joins")
		dc.write_slots_per_day(f, leaves, "Leaves")
		dc.write_slots_per_day(f, timeouts, "Timeouts")

	# Create the diagram
	diag = Diagram("dayconnects", "Connects during a day", 1500, 600)
	diag.xlabel = "Daytime"
	diag.ylabel = "Connects"
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
	diag.plots = ["index '{0}' using 1:2 title '{0}' smooth csplines".format(t)
		for t in ["Joins", "Leaves", "Timeouts"]]

	diag.render(dc.diagramTemplate)
	dc.generalTab.addDiagram(diag)
