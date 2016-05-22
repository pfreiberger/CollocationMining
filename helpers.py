import numpy as np
import pandas as pd
import json
from time import time
from collections import defaultdict
import sys, traceback
import os
import math
from geopy.distance import VincentyDistance as vincenty
import itertools
import tqdm

def loadCities(amenities_path, citites_path, city = ''):
    groups = {'hindu_temple':'religious_centers',
        'mosque':'religious_centers',
        'place_of_worship' : 'religious_centers',
        'synagogue' : 'religious_centers',
        'church' : 'religious_centers',
        'meal_delivery' : 'restaurant',
        'food' : 'restaurant',
        'meal_takeaway' : 'restaurant',
        'roofing_contractor' : 'construction_contractor',
        'electrician' : 'construction_contractor',
        'plumber' : 'construction_contractor',
        'painter' : 'construction_contractor',
        'general_contractor' : 'construction_contractor',
        'health' : 'doctor',
        'lodging' : 'hotel_and_lodging'
    }

    with open(amenities_path) as outfile:
        amenitiesOldInfo = json.load(outfile)
    amenitiesList = [amenity['Label'] for amenity in amenitiesOldInfo]
    amenitiesIndices = {v: k for k, v in zip(range(len(amenitiesList)), amenitiesList)}

    cities = {}
    for file in os.listdir(citites_path):
        if city == '' or city == file:
            try:
                data = pd.read_csv(citites_path + file)
                for old, new in groups.items():
                    data.loc[data.type_lowest == old,'type_lowest'] = new
                filteredData = data[data.type_lowest.isin(amenitiesList)]
                cities[file.split('.')[0]] = filteredData
            except Exception as e:
                print(e)

    print(sum([len(item) for item in cities.values()]))

    return cities, amenitiesIndices, amenitiesList


def initializeContainers(minLat, minLng, maxLat, maxLng, amenitiesList):
    cityCoords = []
    length = vincenty((minLat, minLng), (maxLat, minLng)).kilometers
    width = vincenty((minLat, minLng), (minLat, maxLng)).kilometers
    cellSize = 2.0

    lngEps = (maxLat - minLat)/length*0.05
    latEps = (maxLng - minLng)/width*0.05

    latCells = int(math.ceil(length/cellSize) + 1)
    lngCells = int(math.ceil(width/cellSize) + 1)

    latStep = (maxLat - minLat)/latCells
    lngStep = (maxLng - minLng)/lngCells

    for lat in range(latCells):
        for lng in range(lngCells):
            cityCoords.append(((minLat + lat*latStep), (minLng + lng*lngStep)))
    cityCoords = np.array(cityCoords).reshape([latCells,lngCells, 2])
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