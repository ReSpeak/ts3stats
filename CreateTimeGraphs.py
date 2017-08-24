#!/usr/bin/env python
import calendar
from datetime import *
import fileinput
from html.parser import HTMLParser
import importlib
import math
import os
from os import path
import pkgutil
import re
import subprocess
import sys
import textwrap
from jinja2 import Environment, FileSystemLoader, select_autoescape

import diags

# START configuration

# Special statistics are only shown for vips
# (insert your and your friends names here)
# E. g. vips = ["MyName", "friend42"]
vips = []
# Merge or rename users
# E. g. merges = [["MyName", "MyNameLaptop"], ...]
merges = []

# Minimum total connection time for the diagram
minTime = timedelta(hours = 10)
# Minimum total connection count for the diagram
minConnects = 8
# Statistics about the TS3AudioBot
botStats = False

# Input folder for server logs
inputFolder = "Logs"
# Input folder for TS3AudioBot logs
inputFolderBot = "BotLogs"
# Output folder
outputFolder = "Result"
# Folder for temporary files
tempFolder = "temp"

# Length of a slot in seconds
slotLength = timedelta(minutes = 10)

# END configuration

# Load configuration from Settings.py
if path.isfile("Settings.py"):
	exec(compile(open("Settings.py").read(), "Settings.py", "exec"))

# The length of a part in seconds
slotsPerDay = int(math.ceil(timedelta(days = 1) / slotLength))

# Enum for connections
CONNECTION_START = 1
CONNECTION_END = 2

def openTempfile(name):
	return open(path.join(tempFolder, name + ".tmp"), "w")

htmlParser = HTMLParser()
def parseName(name):
	return htmlParser.unescape(name)

def timeToString(t):
	secs = t.total_seconds()
	seconds = int(secs % 60)
	minutes = int(secs / 60) % 60
	total_hours = int(secs / 3600)
	hours = total_hours % 24

	days = int(total_hours / 24) % 365
	years = int(total_hours / (24 * 365))

	res = ""
	if years > 0:
		res += "{0} years ".format(years)
	if years > 0 or days > 0:
		res += "{0} days ".format(days)
	if years > 0 or days > 0 or hours > 0:
		res += "{0:02}:".format(hours)
	return res + "{0:02}:{1:02}".format(minutes, seconds)

def timestampToString(timestamp):
	date = datetime.fromtimestamp(timestamp)
	return "{0:%Y-%m-%d}".format(date)

def to_slot_index(t, slotLength = slotLength):
	return timedelta(hours = t.hour, minutes = t.minute, seconds = t.second) // slotLength

gnuplotEscapes = ['\\', '^', '_', '@', '&', '~', '{']
def gnuplotEscape(text):
	for c in gnuplotEscapes:
		text = text.replace(c, '\\' + c)
	# Escape twice...
	text = text.replace('\\', '\\\\')
	return text

class DiagramCreator:
	def __init__(self):
		self.env = Environment(loader = FileSystemLoader("."),
			autoescape = select_autoescape(["html", "xml"],
				default_for_string = True),
			trim_blocks = True,
			lstrip_blocks = True)
		self.diagramTemplate = self.env.get_template("template.gp")
		self.htmlTemplate = self.env.get_template("template.html")

	def load_meta(self):
		os.makedirs(outputFolder, mode = 0o755, exist_ok = True)
		os.makedirs(tempFolder, mode = 0o755, exist_ok = True)

		self.args2diags()

	def args2diags(self):
		"""Parse the arguments and fill the diags list"""
		# Get all diagrams
		self.diags = []
		package = diags
		prefix = package.__name__ + "."
		for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
			module = importlib.import_module(modname)
			self.diags.append(module)

	def load_data(self):
		self.users = {}
		self.fakeTimeouts = 0
		self.parse_server()
		self.merge()
		if botStats:
			self.parse_bot()

		self.dayCount = (self.endDay - self.startDay).days + 1
		if botStats:
			self.dayCountBot = (self.endDayBot - self.startDayBot).days + 1

		self.generalTab = Tab("General")
		self.vipTab = Tab("VIPs")
		self.tabs = [self.generalTab, self.vipTab]
		if botStats:
			self.botTab = Tab("Bot")
			self.tabs.append(self.botTab)

	def parse_server(self):
		"""Open the log files and store the users and connections"""
		self.startDay = date.today()
		self.endDay = date.today()

		inputFiles = sorted([path.join(inputFolder, f) for f in os.listdir(inputFolder)
			if path.isfile(path.join(inputFolder, f))])
		linePattern = re.compile(r"^(?P<Date>\d{4}-\d{2}-\d{2})\s+(?P<Time>\d{2}:\d{2}:\d{2}.\d{6})\|\s*(?P<LogLevel>\w+)\s*\|\s*(?P<Initiator>\w+)\s*\|\s*(?P<VServ>\w+)\s*\|\s*client (?P<Action>(?:dis)?connected) '(?P<Name>.*)'\(id:(?P<DbId>\d+)\) (?:reason 'reasonmsg=?(?P<Reason>.*)')?.*\n?$")
		# Read connections from log
		for file in inputFiles:
			with open(file) as f:
				# Previous line
				prevline = ""
				for line in f:
					# Remove the bom
					if line.startswith("\ufeff"):
						line = line[1:]
					match = linePattern.fullmatch(line)
					if match:
						connected = match.group("Action") == "connected"
						# Get time
						t = datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo = timezone.utc).astimezone()
						if t.date() < self.startDay:
							self.startDay = t.date()

						userId = match.group("DbId")
						# Find or create the user
						if userId not in self.users:
							u = User(parseName(match.group("Name")))
							self.users[userId] = u
						else:
							u = self.users[userId]

						# True if the line is a connect
						if connected:
							u.lastConnected.append(t)
						elif u.lastConnected:
							# Ignore clients that didn't connect
							timeout = False
							if match.group("Reason") == "connection lost":
								# Check if it is a timeout
								if "ping timeout" in prevline or "resend timeout" in prevline or t < datetime(2017, 3, 1, tzinfo = timezone.utc):
									timeout = True
								else:
									self.fakeTimeouts += 1
							con = Connection(u.lastConnected[0], t, timeout)
							u.connections.append(con)
							del u.lastConnected[0]
					prevline = line

			# Disconnect all connected clients because the log is finished.
			# Use the last known timestamp for the end
			for u in self.users.values():
				for start in u.lastConnected:
					con = Connection(start, t)
					u.connections.append(con)
				u.lastConnected = []

	def parse_bot(self):
		"""Open the bot log files and store the users and plays"""
		self.startDayBot = date.today()
		self.endDayBot = date.today()

		inputFiles = sorted([path.join(inputFolderBot, f) for f in os.listdir(inputFolderBot)
			if path.isfile(path.join(inputFolderBot, f))])
		linePattern = re.compile(r"^\[(?P<Time>\d{2}:\d{2}:\d{2})\]\s*Debug: MB Got message from (?P<Name>[^:]*): !(?P<Command>.*)\n?$")
		datePattern = re.compile(r"^\[(?P<Time>\d{2}:\d{2}:\d{2})\]\s*Info: \[=== (?:Date:.*,\s*(?P<mday0>\d+) (?P<month0>\w+) (?P<year0>\d+).*|Date:.*,\s*(?P<month1>\w+) (?P<mday1>\d+), (?P<year1>\d+).*|Date/Time:.*,\s*(?P<month2>\w+) (?P<mday2>\d+), (?P<year2>\d+).*)\n?$")
		timePattern = re.compile(r"^\[(?P<Time>\d{2}:\d{2}:\d{2})\].*\n?$")
		# Line formats:
		# [04:44:57]   Info: [=== Date:            Monday, 27 March 2017 ===]
		# [19:31:50]   Info: [=== Date/Time: Friday, August 18, 2017 7:31:50 PM
		# [17:13:54]  Debug: MB Got message from Hengo: !pl [URL]https://www.youtube.com/watch?v=d_RjwMZItZo[/URL]
		# Read connections from log
		for file in inputFiles:
			with open(file) as f:
				curDate = None
				for line in f:
					# Remove the bom
					if line.startswith("\ufeff"):
						line = line[1:]
					match = datePattern.fullmatch(line)
					if match:
						for i in range(3):
							if match.group("year" + str(i)) != None:
								curDate = datetime.strptime("{}-{}-{} {}".format(match.group("year" + str(i)), match.group("month" + str(i)), match.group("mday" + str(i)), match.group("Time")), "%Y-%B-%d %H:%M:%S")
								break
					elif "Date" in line and "[=" in line:
						print("Unknown date format:", line)
					match = timePattern.fullmatch(line)
					if match:
						curTime = datetime.strptime(match.group("Time"), "%H:%M:%S").time()
						if type(curDate) is datetime:
							if curTime < curDate.time():
								curDate += timedelta(days = 1)
							curDate = datetime.combine(curDate.date(), curTime)
						else:
							curDate = curTime

					match = linePattern.fullmatch(line)
					if match:
						if type(curDate) is datetime and curDate.date() < self.startDayBot:
							self.startDayBot = curDate.date()

						cmd = match.group("Command")
						playCmd = cmd.startswith("pl") or cmd.startswith("py") or cmd.startswith("ad")

						# Find or create the user
						name = match.group("Name").strip()
						user = None
						for u in self.users:
							if u.name == name:
								user = u
								break

						if user == None:
							user = User(name)
							self.users.append(user)

						if playCmd:
							user.botPlays.append((curDate, cmd))
						else:
							user.botCommands.append((curDate, cmd))

	def merge(self):
		# Merge users
		for u in self.users.values():
			for m in merges:
				if u.name in m:
					u.name = m[0]

		# Aggregate users with the same name
		self.users = list(self.users.values())
		i = 0
		while i < len(self.users):
			j = i + 1
			while j < len(self.users):
				if self.users[i].name == self.users[j].name:
					# Merge users
					self.users[i].connections += self.users[j].connections
					del self.users[j]
					j -= 1
				j += 1
			i += 1
		print("User count: {}".format(len(self.users)), file = sys.stderr)

		# Select vip users
		self.vip = [u for u in self.users if u.name in vips]

	def create_diagrams(self):
		for diag in self.diags:
			diag.create_diag(self)

		# Render the html
		with open(path.join(outputFolder, "index.html"), "w") as f:
			f.write(self.htmlTemplate.render(tabs = self.tabs,
				date = datetime.now().strftime("%d.%m.%Y %H:%M")))

		# Link the static data
		if not path.exists(path.join(outputFolder, "static")):
			os.symlink("../static", path.join(outputFolder, "static"))

	def fun_per_connected_slot(self, users, slotFun, slotLength = timedelta(days = 1), floorFun = None):
		"""Calls f for each day a certain connection lasts.
		userStart/End are called before and after the connections of a user are worked on.
		slotType is a bit field of CONNECTION_START/END
		start and end are relative to the slotStart
		f(user, connection, slotStart, slotType, start, end)"""
		if floorFun == None:
			# Round down to the nearest multiple of the slotLength time
			floorFun = lambda t: t - timedelta(hours = t.hour, minutes = t.minute, seconds = t.second) % slotLength
		for u in users:
			for c in u.connections:
				# The start of the first slot
				slotStart = floorFun(c.start)
				slotEnd = slotStart + slotLength

				# First slot
				relStart = c.start - slotStart
				if c.end > slotEnd:
					slotFun(u, c, slotStart, CONNECTION_START, relStart, slotLength)
				else:
					# Only one slot
					slotFun(u, c, slotStart, CONNECTION_START | CONNECTION_END, relStart, c.end - slotStart)
					continue

				slotStart = slotEnd
				slotEnd += slotLength
				# For each slot
				while c.end > slotEnd:
					slotFun(u, c, slotStart, 0, timedelta(), slotLength)
					slotStart = slotEnd
					slotEnd += slotLength

				# Last slot
				slotFun(u, c, slotStart, CONNECTION_END, timedelta(), c.end - slotStart)

	def write_slots_per_day(self, f, slots, name = None):
		if name != None:
			f.write("# {0}\n".format(name))
		for i, data in enumerate(slots):
			minutes = int((i * slotLength).total_seconds()) // 60
			f.write("{0:02}:{1:02}\t{2}\n".format(minutes // 60, minutes % 60, data))
		f.write("24:00\t{0}\n\n\n".format(slots[0]))

	def write_days(self, f, days, name = None, cumulative = False, start = None):
		if name != None:
			f.write("# {0}\n".format(name))
		if start == None:
			start = self.startDay
		day = start
		if cumulative:
			sum = 0
		for data in days:
			if cumulative:
				sum += data
				f.write("{0:%d.%m.%Y}\t{1}\n".format(day, sum))
			else:
				f.write("{0:%d.%m.%Y}\t{1}\n".format(day, data))
			day += timedelta(days = 1)
		f.write("\n\n")

class Connection:
	def __init__(self, start, end, timeout = False):
		# Unix timestamp
		self.start = start
		self.end = end
		self.timeout = timeout

	def duration(self):
		return self.end - self.start

class User:
	def __init__(self, name):
		self.name = name
		# Didn't connect so far
		self.lastConnected = []
		# List of connections
		self.connections = []
		self.botPlays = []
		self.botCommands = []

class Diagram:
	diagrams = []
	def __init__(self, filename, title = "Title", width = 1920, height = 600, shortname = None):
		self.filename = filename
		if shortname == None:
			shortname = filename
		self.shortname = shortname
		self.title = title
		self.width = width
		self.height = height
		self.xlabel = "x"
		self.ylabel = "y"
		self.appendText = ""
		self.legend = "left"
		# plots can be set to none to disable them
		self.plots = []

		self.subtitle = None

	def __iter__(self):
		yield "color", "#bbbbbb"
		yield "filename", self.filename
		yield "outputfile", path.join(outputFolder, self.filename)
		yield "shortname", self.shortname
		yield "title", self.title
		if self.subtitle != None:
			yield "subtitle", self.subtitle
		yield "width", self.width
		yield "height", self.height
		yield "xlabel", self.xlabel
		yield "ylabel", self.ylabel
		yield "legend", self.legend
		yield "appendText", textwrap.dedent(self.appendText)
		if self.plots:
			dataFile = "'{0}.tmp' ".format(path.join(tempFolder, self.filename))
			yield "plots", "plot " + ", \\\n\t".join([dataFile + p for p in self.plots])

	def render(self, diagramTemplate):
		# Read the template
		with open("template.gp") as f:
			template = f.read()
		# Create the gnuplot script
		tempName = path.join(tempFolder, self.filename + ".gp.tmp")
		with open(tempName, "w") as f:
			f.write(diagramTemplate.render(dict(self)))

		subprocess.Popen(["gnuplot", tempName])
		if self.subtitle:
			print(self.subtitle, file = sys.stderr)
		Diagram.diagrams.append(self)

class Tab:
	def __init__(self, name, shortname = None):
		self.name = name
		if shortname == None:
			shortname = name
		self.shortname = shortname
		self.diagrams = []

	def addDiagram(self, diag):
		self.diagrams.append(diag)

	def __iter__(self):
		yield "name", self.name
		yield "shortname", self.shortname
		yield "diagrams", [dict(d) for d in self.diagrams]

def main():
	dc = DiagramCreator()
	dc.load_meta()
	dc.load_data()
	dc.create_diagrams()

if __name__ == '__main__':
	main()
