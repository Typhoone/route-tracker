import requests
import pprint
import math
import json  

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
    print(jsonOb)

    response = requests.post(url, json=postData)
    # pp.pprint(response.json()[0])
    return response.json()

pp = pprint.PrettyPrinter(indent=2)
loops = loop_route_lookup(1000, 11213, True, 23, 30, 0, 20000)[:5]

for loop in loops:
    p1 = [loop['userSystem']['x'], loop['userSystem']['y'], loop['userSystem']['z']]
    p2 = [loop['oneSystem']['x'], loop['oneSystem']['y'], loop['oneSystem']['z']]
    p3 = [loop['twoSystem']['x'], loop['twoSystem']['y'], loop['twoSystem']['z']]
    dist1 = round(math.dist(p1, p2), 2)
    dist2 = round(math.dist(p1, p3), 2)
    dist = dist1 if dist1 < dist2 else dist2
    b1 = loop['twoSellListing']['sell_price'] - loop['oneBuyListing']['buy_price']
    b2 = loop['oneSellListing']['sell_price'] - loop['twoBuyListing']['buy_price']
    prof = b1 + b2
    b1Str = str(b1).rjust(5)
    b2Str = str(b2).rjust(5)
    profStr = str(prof).rjust(5)
    distStr = str(dist).rjust(8)

    station1Type = loop['oneStation']['type_id']
    station2Type = loop['twoStation']['type_id']

    # IF planet
    if station1Type >= 13 and station1Type <= 17:
        station1TypeIcon = "🪐"
    else:
        station1TypeIcon = "  "
    if station2Type >= 13 and station2Type <= 17:
        station2TypeIcon = "🪐"
    else:
        station2TypeIcon = "  "


    print(station1TypeIcon, b1Str,"Cr +", station2TypeIcon, b2Str, "Cr =",profStr ,"Cr ", distStr, "ly")


