from CreateTimeGraphs import *

def create_diag(dc):
	"""Time spent on TeamSpeak per user"""
	globalTime = timedelta()
	for u in dc.users:
		# Time in seconds
		u.time = timedelta()
		for con in u.connections:
			# Increase connected time
			u.time += con.duration()
	us = sorted(dc.users, key = lambda u: -u.time)
	for u in us:
		globalTime += u.time
	us = us[:maxUsers]

	# Create users graph
	with openTempfile("usertime") as f:
		for u in us:
			# Time in days
			f.write('"{0}"\t{1}\n'.format(gnuplotEscape(u.name), u.time / timedelta(days = 1)))

	# Create the diagram
	diag = Diagram("usertime", "Time spent on TeamSpeak", 1920, 800)
	diag.xlabel = "User"
	diag.ylabel = "Connection time (in days)"
	diag.legend = "right"
	diag.appendText = """\
		set timefmt "%H:%M:%S"
		set format x "%H:%M:%S"

		set yrange [0:]
		set xtics rotate by -90
		set style histogram clustered gap 4
		set boxwidth 0.8 relative
		"""
	diag.plots.append("using 0:2:xticlabels(1) title 'Time' with boxes")
	diag.subtitle = "Sum of all time spent on this server: {0}".format(timeToString(globalTime))
	diag.render(dc.diagramTemplate)
	dc.generalTab.addDiagram(diag)
