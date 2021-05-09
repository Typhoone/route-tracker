import sys
import tkinter as tk
import requests
from ttkHyperlinkLabel import HyperlinkLabel
import myNotebook as nb
from config import config
import json
from os import path

this = sys.modules[__name__]  # For holding module globals

this.version = 'v0.0.1'

def checkVersion():
    # TODO
	return 1

def plugin_start3(plugin_dir):
	# Read in item names on startup
	this.newest = checkVersion()
	return "Route tracker"

def plugin_app(parent):
	# Adds to the main page UI
	this.frame = tk.Frame(parent)
	this.title = tk.Label(this.frame, text="Route Tracker")
	this.updateIndicator = HyperlinkLabel(this.frame, text="Update availabe", anchor=tk.W, url='https://github.com/Typhoone/route-tracker')
	this.trackerFrame = tk.Label(this.frame)
	this.title.grid(row = 0, column = 0)
	if this.newest == 0:
		this.updateIndicator.grid(padx = 5, row = 0, column = 1)
	return this.frame

def plugin_prefs(parent, cmdr, is_beta):
	# Adds page to settings menu
	frame = nb.Frame(parent)
	HyperlinkLabel(frame, text="Route Tracker {}".format(this.version), background=nb.Label().cget('background'), url="https://github.com/Typhoone/route-tracker").grid()
	return frame

def prefs_changed(cmdr, is_beta):
	fooBarBaz = 0

def journal_entry(cmdr, is_beta, system, station, entry, state):
	fooBarBaz = 0

def update_display():
	fooBarBaz = 0