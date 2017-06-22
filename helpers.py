import numpy as np
import pandas as pd
import json
from time import time
from collections import defaultdict
import sys, traceback
import os
from geopy.geocoders import Nominatim
import math
from geopy.distance import VincentyDistance as vincenty
from geopy.location import Location
import itertools



def load_city():
    data = pd.read_csv("./osm_data/amenities.csv", sep=",", header=0, index_col=0)
    data.columns=["longitude", "latitude", "type", "wheelchair"]
    with open("groups.json", "r") as file:
        groups = json.load(file)
    #data = pd.read_csv('Boston/revised/data/processing_data/result/' + file)
    #data.columns = ['latitude','longitude','intensity','type','clusterId']
 
    for old, new in groups.items():
        data.loc[data.type == old,'type'] = new
   
    data.drop('wheelchair', axis = 1, inplace = True)
    data['id'] = data.index
    data = data.drop_duplicates(['latitude','longitude','type'])

    data["location"]=data.apply(lambda x: (x['latitude'], x['longitude']), axis=1)
    
    
    sizes = data.groupby("type").size()         
    
    amenitiesList = [amenity for amenity, value in sizes.iteritems() if value >= 15]
    amenitiesIndices = {v: k for k, v in zip(range(len(amenitiesList)), amenitiesList)}
    filteredData = data[data.type.isin(amenitiesList)]

    filteredData = filteredData.reset_index(drop=True)
    return {'Copenhagen': filteredData} , amenitiesIndices, amenitiesList

def initializeContainers(minLat, minLng, maxLat, maxLng, amenitiesList):
    cityCoords = []
    length = vincenty((minLat, minLng), (maxLat, minLng)).kilometers
    width = vincenty((minLat, minLng), (minLat, maxLng)).kilometers
    cellSize = 2.0
    latCells = int(math.ceil(length/cellSize) + 1)
    lngCells = int(math.ceil(width/cellSize) + 1)


    lngEps = (maxLat - minLat)/length*0.05
    latEps = (maxLng - minLng)/width*0.05

    latStep = (maxLat - minLat)/latCells
    lngStep = (maxLng - minLng)/lngCells

    for lat in range(latCells):
        for lng in range(lngCells):
            cityCoords.append(((minLat + lat*latStep), (minLng + lng*lngStep)))
    cityCoords = np.array(cityCoords).reshape([latCells,lngCells, 2])
    #hashtable is all zeros
    hashTable = np.zeros([latCells, lngCells, len(amenitiesList)], dtype=object)
    
    return cityCoords, hashTable, lngEps, latEps

def checkStar(instance, colocation):
    for amenity in colocation[1:]:
        if not amenity in [location[2] for location in instance[1]]:
            return False
    return True

def checkClique(locations):
    for location in locations:
        for location2 in locations:
            assert(vincenty(location, location2).meters <= 50)
            if vincenty(location, location2).meters > 50:
                print("No.")

def generateCandidates(colocations, amenities, k0):
    candidates = []
    for colocation in colocations:
        for amenity in amenities[amenities.index(colocation[-1])+1:]:
            notPrevalent = False
            for subPattern in itertools.combinations(colocation + [amenity], k0):
                if not list(subPattern) in colocations:
                    notPrevalent = True
                    break
            if notPrevalent:
                continue
            candidates.append(colocation + [amenity])
    return candidates

def asRadians(degrees):
    return degrees * math.pi / 180

def getXYpos(relativeNullPoint, p):
    """ Calculates X and Y distances in meters.
    """
    deltaLatitude = p.latitude - relativeNullPoint.latitude
    deltaLongitude = p.longitude - relativeNullPoint.longitude
    latitudeCircumference = 40075160 * math.cos(asRadians(relativeNullPoint.latitude))
    resultX = deltaLongitude * latitudeCircumference / 360
    resultY = deltaLatitude * 40008000 / 360
    return resultX, resultY

def checkDist(location1, location2, thres):
    return math.sqrt(pow(location1[2]-location2[2],2)+pow(location1[3] - location2[3],2)) < thres