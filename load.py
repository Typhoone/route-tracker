import sys
import tkinter as tk
import requests
from ttkHyperlinkLabel import HyperlinkLabel
import myNotebook as nb
from config import config
import json
from os import path
from EDMCLogging import get_main_logger
from threading import Lock, Thread
import time
import math
from functools import partial
import time
from theme import theme

this = sys.modules[__name__]  # For holding module globals
this.version = 'v0.0.1'
logger = get_main_logger()

# Loop Vars
WORKER_WAIT_TIME = 3  # Minimum time for worker to wait between sends
this.shouldFetchLoop = False
this.loops = []
this.commoditiesDict = []

this.fetchString = tk.StringVar()


def checkVersion():
    # TODO
	return 1

def plugin_start3(plugin_dir):
	# TODO: does this need a thread?
	this.commoditiesDict = requests.get('https://eddb.io/archive/v6/commodities.json').json()
	logger.debug('Starting worker thread...')
	this.thread = Thread(target=loopFetchThread, name='Loop Fetching worker')
	this.thread.daemon = True
	this.thread.start()
	logger.debug('Done.')
	return "Route Tracker"

def addHomeFrame():
	loop_btn = tk.Button(this.frame, text="Loop Route", command=loadLoops)
	loop_btn.grid(row=1, column=0, sticky=tk.W)

def loadLoops(generate = False):
	if generate == False:
		showPage("loadLoops")
	else:
		this.currentPage = 'showLoops'
		this.loadingLable = tk.Label(this.frame, text="Loading...")
		this.loadingLable.grid(row = 1, column = 0)
		theme.update(this.frame)
		reloadData()

def timeAgoFromListing(listing):
	now = round(time.time())
	listingTime = listing['collected_at']
	timeDiff = now - listingTime
	
	if timeDiff < 60:
		return f"{timeDiff}sec "
	elif timeDiff < 3600:
		return f"{round(timeDiff/60)}min"
	elif timeDiff < 216000:
		return f"{round(timeDiff/60/60)}hrs"
	else:
		return f"{round(timeDiff/60/60/24)}day"

def showLoops():
	logger.debug("Showing Loops")
	numToShow = 5
	topLoops = this.loops[:numToShow]
	rowNum = 1
	for indx, loop in enumerate(topLoops):
		p1 = [loop['userSystem']['x'], loop['userSystem']['y'], loop['userSystem']['z']]
		p2 = [loop['oneSystem']['x'], loop['oneSystem']['y'], loop['oneSystem']['z']]
		p3 = [loop['twoSystem']['x'], loop['twoSystem']['y'], loop['twoSystem']['z']]
		dist1 = round(math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2)+((p1[2]-p2[2])**2) ), 2)
		dist2 = round(math.sqrt( ((p1[0]-p3[0])**2)+((p1[1]-p3[1])**2)+((p1[2]-p3[2])**2) ), 2)
		dist = dist1 if dist1 < dist2 else dist2
		distStr = str(dist).rjust(8)

		b1 = loop['twoSellListing']['sell_price'] - loop['oneBuyListing']['buy_price']
		b2 = loop['oneSellListing']['sell_price'] - loop['twoBuyListing']['buy_price']
		prof = b1 + b2

		profStr = str(prof).rjust(7)

		station1Type = loop['oneStation']['type_id']
		station2Type = loop['twoStation']['type_id']

		# IF planet
		if station1Type >= 13 and station1Type <= 17:
			station1TypeIcon = "🪐".rjust(3)
		else:
			station1TypeIcon = " ".rjust(3)
		if station2Type >= 13 and station2Type <= 17:
			station2TypeIcon = "🪐".rjust(3)
		else:
			station2TypeIcon = " ".rjust(3)

		sup1 = str(loop['oneBuyListing']['supply']).ljust(7)
		sup2 = str(loop['twoBuyListing']['supply']).ljust(7)

		loopDist = (str(round(loop['distance'],2)) + " ly").rjust(12)

		listing1TimeAgo = timeAgoFromListing(loop['oneBuyListing'])
		listing2TimeAgo = timeAgoFromListing(loop['twoBuyListing'])
		line1Text = f'{indx+1}: {listing1TimeAgo} ⮀  {listing2TimeAgo} {profStr}Cr {distStr}ly'
		infoLine1 = tk.Label(this.frame, text=line1Text)
		infoLine1.grid(row = rowNum, column = 0)

		# https://stackoverflow.com/a/22290388
		action_with_arg = partial(showPage, "showLoop", indx)
		showLoopBtn = tk.Button(this.frame, text="Select", command=action_with_arg)
		showLoopBtn.grid(row=rowNum, column=1, sticky=tk.W)

		rowNum = rowNum + 1

		line2Text = f'{station1TypeIcon}  Sup: {sup1} ⮀ {station2TypeIcon} Sup: {sup2} {loopDist}'
		infoLine2 = tk.Label(this.frame, text=line2Text)
		infoLine2.grid(row = rowNum, column = 0)

		rowNum = rowNum + 1

	addFooter(rowNum, "home")

def getCategoryNameFromCommodityId(id):
    for commodity in this.commoditiesDict:
        if commodity['id'] == id:
            return commodity['category']['name']
    return 'Unknown'

def showSingleLoop(indx):
	this.currentLoopIndx = indx


	loop = this.loops[indx]
	oneSystemName = str(loop['oneSystem']['name'])
	twoSystemName = str(loop['twoSystem']['name'])
	oneStationName = str(loop['oneStation']['name'])
	twoStationName = str(loop['twoStation']['name'])

	oneCommodityName = str(loop['oneCommodity']['name'])
	twoCommodityName = str(loop['twoCommodity']['name'])
	oneCommodityId = loop['oneCommodity']['id']
	twoCommodityId = loop['twoCommodity']['id']
	oneCommodityCategory = getCategoryNameFromCommodityId(oneCommodityId)
	twoCommodityCategory = getCategoryNameFromCommodityId(twoCommodityId)

	sup1 = str(loop['oneBuyListing']['supply'])
	sup2 = str(loop['twoBuyListing']['supply'])

	station1Type = loop['oneStation']['type_id']
	station2Type = loop['twoStation']['type_id']

	b1 = str(loop['twoSellListing']['sell_price'] - loop['oneBuyListing']['buy_price'])
	b2 = str(loop['oneSellListing']['sell_price'] - loop['twoBuyListing']['buy_price'])

	# printRoute(oneSystemName, oneStationName, b1, station1Type)

	# IF planet
	if station1Type >= 13 and station1Type <= 17:
		station1TypeIcon = "🪐"
	else:
		station1TypeIcon = " "
	if station2Type >= 13 and station2Type <= 17:
		station2TypeIcon = "🪐"
	else:
		station2TypeIcon = " "

	loopOneStationLine1Text = f'{(oneSystemName + ": " + oneStationName).ljust(30)} {(b1 + "Cr").rjust(10)} {station1TypeIcon}'
	loopOneStationLine2Text = f'{oneCommodityCategory.ljust(20)} {oneCommodityName.ljust(20)} x {sup1.rjust(6)}'

	loopOneStationLine1 = tk.Label(this.frame, text=loopOneStationLine1Text)
	loopOneStationLine1.grid(row = 1, column = 0)

	loopOneStationLine2 = tk.Label(this.frame, text=loopOneStationLine2Text)
	loopOneStationLine2.grid(row = 2, column = 0)


	loopTwoStationLine1Text = f'{(twoSystemName + ": " + twoStationName).ljust(30)} {(b2 + "Cr").rjust(10)} {station2TypeIcon}'
	loopTwoStationLine2Text = f'{twoCommodityCategory.ljust(20)} {twoCommodityName.ljust(20)} x {sup2.rjust(6)}'

	loopTwoStationLine1 = tk.Label(this.frame, text=loopTwoStationLine1Text)
	loopTwoStationLine1.grid(row = 4, column = 0)

	loopTwoStationLine2 = tk.Label(this.frame, text=loopTwoStationLine2Text)
	loopTwoStationLine2.grid(row = 5, column = 0)

	addFooter(6, "showLoops")

def printRoute(systemName, stationName, cost, stationType):
	# IF planet
	if stationType >= 13 and stationType <= 17:
		stationTypeIcon = "🪐"
	else:
		stationTypeIcon = " "

def reloadData():
	this.fetchString.set("Loading...")
	this.shouldFetchLoop = True
	this.reloadBtn["state"] = "disabled"

def addFooter(rowNum, backPage):
	this.fetchString.set("Fetch Update")
	action_with_arg = partial(showPage, backPage)
	showLoopBtn = tk.Button(this.frame, text="Back", command=action_with_arg)
	showLoopBtn.grid(row=rowNum, column=0, sticky=tk.W)

	this.reloadBtn = tk.Button(this.frame, textvariable=this.fetchString, command=reloadData)
	this.reloadBtn.grid(row=rowNum, column=2, sticky=tk.W)

def showPage(page, extData = "null"):
	logger.debug("Show Page: " + page)
	for widget in this.frame.winfo_children():
			widget.destroy()
	this.title = tk.Label(this.frame, text="Route Tracker")
	this.title.grid(row = 0, column = 0)
	this.currentPage = page
	if page == 'home':
		addHomeFrame()
	elif page == 'loadLoops':
		loadLoops(True)
	elif page == "showLoops":
		logger.debug("Showing Loops page")
		showLoops()
	elif page == "showLoop":
		logger.debug("Showing loop: " + str(extData))
		if extData == "null":
			showSingleLoop(this.currentLoopIndx)
		else:
			showSingleLoop(extData)
	else:
		logger.error('Unknown Page: ' + page)
	theme.update(this.frame)

def plugin_app(parent):
	# Adds to the main page UI
	this.frame = tk.Frame(parent)
	showPage("home")
	return this.frame

def plugin_prefs(parent, cmdr, is_beta):
	"""Plugin Preferences UI hook."""
	x_padding = 10
	x_button_padding = 12  # indent Checkbuttons and Radiobuttons
	y_padding = 2		# close spacing

	frame = nb.Frame(parent)
	frame.columnconfigure(1, weight=1)

	HyperlinkLabel(
        frame, text='Route Tracker', background=nb.Label().cget('background'), url="https://github.com/Typhoone/route-tracker", underline=True
    ).grid(columnspan=2, padx=x_padding, sticky=tk.W)  # Don't translate

	# this.includePlanetary = tk.IntVar(True)
	# this.includePlanetary_button = nb.Checkbutton(
    #     frame, text=_('Include Planetary'), variable=this.includePlanetary, command=prefsvarchanged
    # )
	# this.includePlanetary_button.grid(columnspan=2, padx=x_button_padding, pady=(5, 0), sticky=tk.W)
	

	return frame

def prefs_changed(cmdr, is_beta):
	logger.debug("Prefs Changed")

def prefsvarchanged():
	"""Preferences window change hook."""
	logger.debug("Prefs Changed func called")
	logger.debug(this.includePlanetary_button['state'])
	logger.debug(this.includePlanetary.get())
	
	state = tk.DISABLED
	if this.includePlanetary.get():
		state = this.includePlanetary_button['state']

	# this.label['state'] = state
	# this.apikey_label['state'] = state
	# this.apikey['state'] = state

def journal_entry(cmdr, is_beta, system, station, entry, state):
	logger.debug("Journal Entry")

def update_display():
	logger.debug("Update Display")

def loop_route_lookup(minSupply, systemId, includePlanetary, hopDist=50, priceAge=30, minDemand=0, minProfit=9500):
    url = 'https://eddb.io/route/search/loops'
    postData = {
                "loopsSettings": {
                    "implicitCommodities": [],
                    "ignoredCommodities": [],
                    "hopDistance": hopDist,
                    "minSupply": minSupply,
                    "minDemand": minDemand,
                    "priceAge": priceAge,
                    "minProfit": minProfit,
                    "systemId": systemId,
                    "sort": "profit"
                },
                "systemFilter": {
                    "skipPermit": False,
                    "powers": []
                },
                "stationFilter": {
                    "landingPad": 30,
                    "governments": [],
                    "allegiances": [],
                    "states": [],
                    "economies": [],
                    "distance": None,
                    "loopDistance": 0,
                    "singleRouteDistance": 0,
                    "includePlanetary": includePlanetary,
                    "includeFleetCarriers": False
                }
            }

    jsonOb = json.dumps(postData, indent = 4)
    # print(jsonOb)
    logger.debug("Begin Fetch")
    response = requests.post(url, json=postData)
    logger.debug("End Fetch")
    return response.json()

def loopFetchThread():
	logger.debug('Starting...')
	while True:
		if this.shouldFetchLoop == True:
			this.shouldFetchLoop = False
			logger.debug("Fetching Loop Data")
			this.loops = loop_route_lookup(1000, 11213, True, 23, 30, 0, 20000)
			logger.debug("Loop Data Fetched")
			showPage(this.currentPage)
		else:
			time.sleep(3)