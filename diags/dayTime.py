from CreateTimeGraphs import *

def create_diag(dc):
	"""Time spent during a day (vip)"""
	# Global connections times
	# Times: The time for each slot
	vipTimes = [timedelta()] * slotsPerDay
	globalTimes = [timedelta()] * slotsPerDay

	# Initialize fields for users
	for u in dc.vip:
		# Times: The time for each slot
		u.times = [timedelta()] * slotsPerDay

	def f(u, con, slotStart, slotType, start, end):
		seconds = timedelta(hours = slotStart.hour,
			minutes = slotStart.minute,
			seconds = slotStart.second)
		index = seconds // slotLength
		u.times[index] += end - start

	dc.fun_per_connected_slot(dc.vip, f, slotLength)

	for u in dc.vip:
		# Accumulate vipTimes
		for i, d in enumerate(u.times):
			vipTimes[i] += d

	with openTempfile("daytime") as f:
		for u in dc.vip:
			dc.write_slots_per_day(f, [t / timedelta(hours = 1) for t in u.times], u.name)

		# Write global times
		dc.write_slots_per_day(f, [t / len(dc.vip) / timedelta(hours = 1) for t in vipTimes], "VIP average")
		#dc.write_slots_per_day(f, [t / len(users) / timedelta(hours = 1) for t in globalTimes], "Average")

	# Create the diagram
	diag = Diagram("daytime", "Daytime", 1500, 600)
	diag.xlabel = "Daytime"
	diag.ylabel = "Time (in hours)"
	diag.legend = "at graph 0.2, 0.95"
	diag.appendText = """\
		set timefmt "%H:%M"
		set format x "%H:%M"
		set xdata time
		set xrange ["00:00":"24:00"]

		set style data lines
		set key autotitle columnhead
		set samples 100
		"""
	diag.plots = ["index '{0}' using 1:2 title '{0}'"
		.format(u.name) for u in dc.vip]
	diag.plots.append("index 'VIP average' using 1:2 title 'Average'")
	#diag.plots.append("index 'Average' using 1:2 title 'Average'")

	diag.render(dc.diagramTemplate)
	dc.vipTab.addDiagram(diag)
