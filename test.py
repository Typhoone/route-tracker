import requests
import math
import json  
import sys
from os import system, name

this = sys.modules[__name__]  # For holding module globals

this.loops = []
this.commoditiesDict = []
this.destNumber = 0

def initFunc():
    clear()
    this.commoditiesDict = requests.get('https://eddb.io/archive/v6/commodities.json').json()
# define our clear function
def clear():
  
    # for windows
    if name == 'nt':
        _ = system('cls')
  
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

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
    print("Loading...")
    response = requests.post(url, json=postData)
    # pp.pprint(response.json()[0])
    clear()
    return response.json()

def showTopLoops(top=5):
    topLoops = this.loops[:top]

    for indx, loop in enumerate(topLoops):
        p1 = [loop['userSystem']['x'], loop['userSystem']['y'], loop['userSystem']['z']]
        p2 = [loop['oneSystem']['x'], loop['oneSystem']['y'], loop['oneSystem']['z']]
        p3 = [loop['twoSystem']['x'], loop['twoSystem']['y'], loop['twoSystem']['z']]
        dist1 = round(math.dist(p1, p2), 2)
        dist2 = round(math.dist(p1, p3), 2)
        dist = dist1 if dist1 < dist2 else dist2
        b1 = loop['twoSellListing']['sell_price'] - loop['oneBuyListing']['buy_price']
        b2 = loop['oneSellListing']['sell_price'] - loop['twoBuyListing']['buy_price']
        prof = b1 + b2
        b1Str = str(b1).rjust(6)
        b2Str = str(b2).rjust(5)
        profStr = str(prof).rjust(5)
        distStr = str(dist).rjust(8)

        station1Type = loop['oneStation']['type_id']
        station2Type = loop['twoStation']['type_id']

        # IF planet
        if station1Type >= 13 and station1Type <= 17:
            station1TypeIcon = "🪐"
        else:
            station1TypeIcon = " "
        if station2Type >= 13 and station2Type <= 17:
            station2TypeIcon = "🪐"
        else:
            station2TypeIcon = " "
        print(str(indx+1).rjust(2), ":", b1Str,"Cr +",  b2Str, "Cr =",profStr ,"Cr ", distStr, "ly")

        sup1 = str(loop['oneBuyListing']['supply'])
        sup2 = str(loop['twoBuyListing']['supply'])

        loopDist = (str(round(loop['distance'],2)) + " ly").rjust(12)

        print(station1TypeIcon.rjust(3), "Sup:", sup1.rjust(6),"  ⮀", station2TypeIcon.rjust(2), "Sup: ", sup2.rjust(6), loopDist)
        print("-" * 50)

def getCategoryNameFromCommodityId(id):
    for commodity in this.commoditiesDict:
        if commodity['id'] == id:
            return commodity['category']['name']
    return 'Unknown'


def printLoop(indx):
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

    # IF planet
    if station1Type >= 13 and station1Type <= 17:
        station1TypeIcon = "🪐"
    else:
        station1TypeIcon = " "
    if station2Type >= 13 and station2Type <= 17:
        station2TypeIcon = "🪐"
    else:
        station2TypeIcon = " "
    
    # Print out Loop
    print("\033[0m", end = '')
    if this.destNumber == 0:
        print("\033[1m", end = '')
    print((oneSystemName + ": " + oneStationName).ljust(30), (b1 + "Cr").rjust(10), station1TypeIcon)
    print(oneCommodityCategory.ljust(20), oneCommodityName.ljust(20), "x", sup1.rjust(6))
    print("\033[0m", end = '')
    print("-" * 50)
    if this.destNumber == 1:
        print("\033[1m", end = '')
    print((twoSystemName + ": " + twoStationName).ljust(30), (b2 + "Cr").rjust(10), station2TypeIcon)
    print(twoCommodityCategory.ljust(20), twoCommodityName.ljust(20), "x", sup2.rjust(6))
    print("\033[0m", end = '')



initFunc()
this.loops = loop_route_lookup(1000, 11213, True, 23, 30, 0, 20000)
showTopLoops()
oldChoice = 0
while True:
    choice = int(input("Select Loop: "))
    clear()
    if choice == 0:
        showTopLoops()
    # Reload data
    elif choice == -1:
        this.loops = loop_route_lookup(1000, 11213, True, 23, 30, 0, 20000)
        showTopLoops()
    # toggle dest
    elif choice == -2:
        this.destNumber ^= 1
        printLoop(oldChoice-1)
    else:
        printLoop(choice-1)
    oldChoice = choice




