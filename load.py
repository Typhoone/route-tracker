# Python Imports
import sys
import tkinter as tk
import requests
import json
import time
import math
import time
import os
import logging
import urllib

from tkinter import ttk
from os import path
from threading import Lock, Thread
from functools import partial

# EDMC imports
import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from config import config, appname
from EDMCLogging import get_main_logger
from theme import theme


# System Vars
this = sys.modules[__name__]  # For holding module globals
this.version = 'v0.0.1'
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

# For compatibility with pre-5.0.0
if not hasattr(config, 'get_int'):
    config.get_int = config.getint
if not hasattr(config, 'get_str'):
    config.get_str = config.get
if not hasattr(config, 'get_bool'):
    config.get_bool = lambda key: bool(config.getint(key))
if not hasattr(config, 'get_list'):
    config.get_list = config.get

# Loop Vars
WORKER_WAIT_TIME = 3  # Minimum time for worker to wait between sends
this.shouldFetchLoop = False
this.loops = []
this.commoditiesDict = []

# Footer Vars
this.fetchString = tk.StringVar()

# EDMC Functions
def checkVersion():
    # TODO
	return 1

def plugin_start3(plugin_dir):
	# TODO: does this need a thread?
	this.commoditiesDict = requests.get('https://eddb.io/archive/v6/commodities.json').json()
	logger.info('Starting worker thread...')
	this.thread = Thread(target=loopFetchThread, name='Loop Fetching worker')
	this.thread.daemon = True
	this.thread.start()
	logger.debug('Done.')
	loadConfigVars()
	return "Route Tracker"

def journal_entry(cmdr, is_beta, system, station, entry, state):

	# logger.debug(entry)

	if entry['event'] == 'Docked':
		this.currentStation = entry['StationName']
		this.currentSystem = entry['StarSystem']
		locChanged()
		reloadData()
	elif entry['event'] == 'FSDJump':
		this.currentSystem = system
		locChanged()
	elif entry['event'] == 'StartUp':
		this.currentStation = entry['StationName']
		this.currentSystem = entry['StarSystem']
		locChanged()



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
    ).grid(row = 0, columnspan=2, padx=x_padding, sticky=tk.W)  # Don't translate

	this.includePlanetary_button = nb.Checkbutton(
        frame, text='Include Planetary', variable=this.includePlanetary
    )
	this.includePlanetary_button.grid(row = 1, columnspan=2, padx=x_button_padding, pady=y_padding, sticky=tk.W)

	this.minSupplyEntry = addEntry(frame, 2, this.minSupplyInt, "x Your Inventory")
	this.hopDistEntry = addEntry(frame, 3, this.hopDistInt, "Hop Distance (0 for your ships max hop)")
	this.priceAgeEntry = addEntry(frame, 4, this.priceAgeInt, "Max Price Age")
	this.minDemandEntry = addEntry(frame, 5, this.minDemandInt, "Min Demand")
	this.minProfitEntry = addEntry(frame, 6, this.minProfitInt, "Min Profit")

	return frame

def locChanged():
	config.set("Route-Tracker_CurrentSystem", this.currentSystem)
	config.set("Route-Tracker_CurrentStation", this.currentStation)

def prefs_changed(cmdr, is_beta):
	logger.debug("Prefs Changed")
	config.set("Route-Tracker_includePlanetary", this.includePlanetary.get())
	config.set("Route-Tracker_MinSupply", str(this.minSupplyInt.get()))
	config.set("Route-Tracker_hopDist", this.hopDistInt.get())
	config.set("Route-Tracker_priceAge", this.priceAgeInt.get())
	config.set("Route-Tracker_minDemand", this.minDemandInt.get())
	config.set("Route-Tracker_minProfit", this.minProfitInt.get())
	# TODO: add an auto update optin in prefs 
	# reloadData()

# Common
def loadConfigVars():
	this.includePlanetary = tk.IntVar(value=config.get_int("Route-Tracker_includePlanetary", default = 1))
	this.minSupplyInt = tk.DoubleVar(value=config.get_str("Route-Tracker_MinSupply", default = 1.5))
	this.hopDistInt = tk.IntVar(value=config.get_int("Route-Tracker_hopDist", default = 0))
	this.priceAgeInt = tk.IntVar(value=config.get_int("Route-Tracker_priceAge", default = 30))
	this.minDemandInt = tk.IntVar(value=config.get_int("Route-Tracker_minDemand", default = 0))
	this.minProfitInt = tk.IntVar(value=config.get_int("Route-Tracker_minProfit", default = 20000))

	this.currentSystem = config.get_str("Route-Tracker_CurrentSystem", default = 'Sol')

	this.currentStation = config.get_str("Route-Tracker_CurrentStation", default = "Abraham Lincoln")

def getCategoryNameFromCommodityId(id):
    for commodity in this.commoditiesDict:
        if commodity['id'] == id:
            return commodity['category']['name']
    return 'Unknown'

def addLabel(text, row, col, frameToUse, alignment=tk.W):
	label = tk.Label(frameToUse, text=text)
	label.grid(row = row, column = col, sticky=alignment)
	return label

def addEntry(frameToPlace, row, entryVar,  labelString = "", alignment=tk.W):
	newEntry = tk.Entry(frameToPlace, exportselection=0, textvariable=entryVar)
	newEntry.grid(row = row, column = 0, sticky=alignment)

	if labelString != "":
		prefLabel = addLabel(labelString, row, 1, frameToPlace)
		prefLabel.configure(bg='white')

	return newEntry	

def reloadData():
	this.fetchString.set("Loading...")
	this.shouldFetchLoop = True
	this.reloadBtn["state"] = "disabled"

def addFooter(rowNum, backPage):
	this.fetchString.set("Fetch Update")
	action_with_arg = partial(showPage, backPage)
	showLoopBtn = tk.Button(this.frame, text="Back", command=action_with_arg)
	showLoopBtn.grid(row=rowNum, column=0, sticky=tk.W, columnspan=3)

	this.reloadBtn = tk.Button(this.frame, textvariable=this.fetchString, command=reloadData)
	this.reloadBtn.grid(row=rowNum, column=2, sticky=tk.E, columnspan=10)

def showPage(page, extData = "null"):
	logger.debug("Show Page: " + page)
	for widget in this.frame.winfo_children():
			widget.destroy()
	this.currentPage = page
	if page == 'home':
		addHomeFrame()
	elif page == 'loadLoops':
		loadLoops(True)
	elif page == "showLoops":
		showLoops()
	elif page == "showLoop":
		if extData == "null":
			showSingleLoop(findLoopIndexByID(this.currentLoopID))
		else:
			showSingleLoop(extData)
	else:
		logger.error('Unknown Page: ' + page)
	theme.update(this.frame)

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

def systemLookup(systemName):
    req = {
        "system[name]": systemName
    }
    encodeReq = urllib.parse.urlencode(req)

    url = f"https://eddb.io/system/search?{encodeReq}"
    response = requests.get(url).json()

    if len(response) == 0:
        return None

    return response

def getSystemId(systemName):
    systems = systemLookup(systemName)
    if systems != None:
        for indx, system in enumerate(systems):
            if system['name'] == systemName:
                return(system['id'])
    else:
        return None

# Home Screen
def addHomeFrame():
	loop_btn = tk.Button(this.frame, text="Loop Route", command=loadLoops)
	loop_btn.grid(row=1, column=0, sticky=tk.W)

# Loop Route
def loadLoops(generate = False):
	if generate == False:
		showPage("loadLoops")
	else:
		this.currentPage = 'showLoops'
		this.loadingLable = tk.Label(this.frame, text="Loading...")
		this.loadingLable.grid(row = 1, column = 0)
		theme.update(this.frame)
		reloadData()

def showLoops():
	numToShow = 5
	topLoops = this.loops[:numToShow]
	addLabel('#', 0, 0, this.frame)
	addLabel('Age', 0, 1, this.frame, tk.E)
	addLabel('/', 0, 2, this.frame)
	addLabel('Supply', 0, 3, this.frame)
	addLabel('Dist (ly)', 0, 4, this.frame, tk.E)
	addLabel('Profit', 0, 5, this.frame, tk.E)
	rowNum = 1
	for indx, loop in enumerate(topLoops):
		p1 = [loop['userSystem']['x'], loop['userSystem']['y'], loop['userSystem']['z']]
		p2 = [loop['oneSystem']['x'], loop['oneSystem']['y'], loop['oneSystem']['z']]
		p3 = [loop['twoSystem']['x'], loop['twoSystem']['y'], loop['twoSystem']['z']]
		dist1 = round(math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2)+((p1[2]-p2[2])**2) ), 2)
		dist2 = round(math.sqrt( ((p1[0]-p3[0])**2)+((p1[1]-p3[1])**2)+((p1[2]-p3[2])**2) ), 2)
		dist = dist1 if dist1 < dist2 else dist2
		distStr = str(dist)

		b1 = loop['twoSellListing']['sell_price'] - loop['oneBuyListing']['buy_price']
		b2 = loop['oneSellListing']['sell_price'] - loop['twoBuyListing']['buy_price']
		prof = b1 + b2

		profStr = str(prof)

		station1Type = loop['oneStation']['type_id']
		station2Type = loop['twoStation']['type_id']

		sup1 = str(loop['oneBuyListing']['supply'])
		sup2 = str(loop['twoBuyListing']['supply'])

		loopDist = str(round(loop['distance'],2))

		listing1TimeAgo = timeAgoFromListing(loop['oneBuyListing'])
		listing2TimeAgo = timeAgoFromListing(loop['twoBuyListing'])

		# Top Line
		addLabel(f'{indx + 1}', rowNum, 0, this.frame)
		addLabel(f'{listing1TimeAgo}', rowNum, 1, this.frame, tk.E)
		addLabel('⮀', rowNum, 2, this.frame)
		addLabel(f'{listing2TimeAgo}', rowNum, 3, this.frame)
		addLabel(f'{distStr}', rowNum, 4, this.frame)
		addLabel(f'{profStr}Cr', rowNum, 5, this.frame)
		rowNum = rowNum + 1

		# Bott line
		if station1Type >= 13 and station1Type <= 17:
			sup1 = f'🪐 {sup1}'
		addLabel(sup1, rowNum, 1, this.frame, tk.E)
		addLabel('⮀', rowNum, 2, this.frame)
		if station2Type >= 13 and station2Type <= 17:
			sup2 = f'{sup2} 🪐'
		addLabel(sup2, rowNum,3, this.frame)
		addLabel(f'{loopDist}', rowNum, 4, this.frame)

		# https://stackoverflow.com/a/22290388
		action_with_arg = partial(showPage, "showLoop", indx)
		showLoopBtn = tk.Button(this.frame, text="Select", command=action_with_arg)
		showLoopBtn.grid(row=rowNum, column=5, sticky=tk.E)

		rowNum = rowNum + 1
		ttk.Separator(this.frame, orient=tk.HORIZONTAL).grid(
                columnspan=10, sticky=tk.EW, row=rowNum
            )
		rowNum = rowNum + 1


	addFooter(rowNum, "home")

def findLoopIndexByID(loopID):
	for indx, loop in enumerate(this.loops):
		if loop['tradeLoopId'] == loopID:
			return indx
	return None

def showSingleLoop(indx):
	if indx == None:
		addLabel("Loop data Missing!", 0, 0, this.frame)
	else:
		this.currentLoopIndx = indx
		loop = this.loops[indx]

		this.currentLoopID = loop['tradeLoopId']

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
		printRoute(oneSystemName, oneStationName, b1, station1Type, 1, oneCommodityCategory, oneCommodityName, sup1)
		
		logger.debug(twoStationName)
		logger.debug(this.currentStation)

		if this.currentStation == twoStationName:
			addLabel("ᐃ", 3, 2, this.frame)
		else:
			addLabel("ᐁ", 3, 2, this.frame)
		
		# addLabel("ᐃ", 3, 3, this.frame)
		printRoute(twoSystemName, twoStationName, b2, station2Type, 4, twoCommodityCategory, twoCommodityName, sup2)

		HyperlinkLabel(
			this.frame, text=f'https://eddb.io/trade/loop/{this.currentLoopID}', url=f'https://eddb.io/trade/loop/{this.currentLoopID}', underline=True
		).grid(row = 6, columnspan=10, sticky=tk.W)

	addFooter(7, "showLoops")

def printRoute(systemName, stationName, cost, stationType, startRow, category, commodity, supply):
	# Top Row
	addLabel(f'{systemName + ": "}', startRow, 0, this.frame)
	# IF planet
	if stationType >= 13 and stationType <= 17:
		addLabel("🪐", startRow, 1, this.frame)
	addLabel(stationName, startRow, 2, this.frame)
	addLabel(f'{cost}Cr', startRow, 3, this.frame, tk.E)

	# Bot Row
	addLabel(category, startRow+1, 0, this.frame)
	addLabel(commodity, startRow+1, 2, this.frame)
	addLabel(f'x{supply}', startRow+1, 3, this.frame, tk.E)

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
    # logger.debug(jsonOb)
    logger.debug("Begin Fetch")
    response = requests.post(url, json=postData)
    logger.debug("End Fetch")
    return response.json()

def loopFetchThread():
	logger.debug('Starting...')
	while True:
		if this.shouldFetchLoop == True:
			if this.currentSystem != None:
				systemId = getSystemId(this.currentSystem)
			else:
				systemId = 17072


			this.shouldFetchLoop = False
			logger.info(f'Fetching Loop Data - {systemId}: {this.currentSystem}')
			maxHopDist = 23
			minSup = round(this.minSupplyInt.get() * 640)
			includePlanet = True if this.includePlanetary.get() == 1 else False
			this.loops = loop_route_lookup(minSup, 
											systemId, 
											includePlanet, 
											maxHopDist, 
											this.priceAgeInt.get(), 
											this.minDemandInt.get(), 
											this.minProfitInt.get()
											)
			logger.info("Loop Data Fetched")
			showPage(this.currentPage)
		else:
			time.sleep(3)