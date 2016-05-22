import numpy as np
from time import time
from collections import defaultdict
import math
from geopy.distance import VincentyDistance as vincenty
import geopy as gp
import itertools
import helpers as hlp
import pandas as pd

patternInstances = []

def hashData(hashTable, data, latCells, lngCells, latStep, lngStep, latEps, lngEps):
    global relPoint
    start = time()
    for index, location in data.iterrows():
        lat, lng = location.location_lat, location.location_lng
        currentLatId, currentLngId = int((lat-minLat)/latStep), int((lng-minLng)/lngStep)

        upperLatId, bottomLatId = int((lat+latEps-minLat)/latStep), int((lat-latEps-minLat)/latStep)
        upperLngId, bottomLngId = int((lng+lngEps-minLng)/lngStep), int((lng-lngEps-minLng)/lngStep)
        otherLatId = upperLatId if upperLatId!=currentLatId else bottomLatId if bottomLatId!=currentLatId else currentLatId
        otherLatId = min(otherLatId, latCells-1)
        otherLngId = upperLngId if upperLngId!=currentLngId else bottomLngId if bottomLngId!=currentLngId else currentLngId
        otherLngId = min(otherLngId, lngCells-1)

        for latId in set([currentLatId, otherLatId]):
            for lngId in set([currentLngId, otherLngId]):
                try:
                    x, y = hlp.getXYpos(relPoint, gp.Point(lat, lng))
                    if hashTable[latId, lngId, amenitiesIndices[location.type_lowest]]:
                        hashTable[latId, lngId, amenitiesIndices[location.type_lowest]].append((lat, lng, x, y))
                        hashTable[latId, lngId, amenitiesIndices[location.type_lowest]].sort(key = lambda x : x[0])
                    else:
                        hashTable[latId, lngId, amenitiesIndices[location.type_lowest]] = [(lat, lng, x, y)]
                except Exception as e:
                    print(e) #pass

    print('Super fast hasing took', time()-start, 'to execute')
    return hashTable, time()-start

def processSet(cur_atype, cur_list, objectDict, patList, localPatterns, thresh, objectset, depth):
    if len(cur_list) == 0:
        return
    newPatList = list(patList)
    newPatList.append(cur_atype)
    newPatList.sort()
    subPattern = '.'.join(newPatList)
    
    localPatterns[subPattern] = 1
    for location in cur_list:
        
        #print('adding new instance of size', len(objectset)+1)
        #newid = len(patternInstances)
        #print("curid",newid)
        #all_locations = [location]
        #patternInstances.append({'latitude': location[0], 'longitude': location[1], 'type': cur_atype, 'pattern': subPattern, 'size': len(newPatList), 'instanceid': newid})
        #add new instance
        #for objtuple in objectset:
        #    all_locations.append(objtuple[1])
        #    patternInstances.append({'latitude': objtuple[1][0], 'longitude': objtuple[1][1], 'type': objtuple[0], 'pattern': subPattern, 'size': len(newPatList), 'instanceid': newid})
        #checkClique(all_locations)
        
        newDict = dict()
        for atype,atype_list in objectDict.items():
            new_list = []
            for obj_loc in atype_list:
                #if vincenty(location, obj_loc).meters <= 50:
                if hlp.checkDist(location, obj_loc, 50):
                    new_list.append(obj_loc)
                    #for old_loc in objectset:
                     #   assert(vincenty(old_loc[1], obj_loc).meters <= 50)
            newDict[atype] = new_list
        while len(newDict) > 0:
            for next_atype, next_list in newDict.items():
                #add object to the pattern instance
                new_objectset = list(objectset)
                new_objectset.append((cur_atype, location))
                del newDict[next_atype]
                processSet(next_atype, next_list, newDict, newPatList, localPatterns, thresh, new_objectset, depth+1)
                break
                
def mineCliquePatterns(hashTable, latCells, lngCells, latStep, lngStep, lngEps):
    global patternInstances
    patterns = defaultdict(lambda: defaultdict(lambda: 0))
    thresh = math.sqrt(latEps**2+lngEps**2)
    start = time()
    tmp = 0
    for lat in range(latCells):
        for lng in range(lngCells):
            print("Processing cell", lat+1, "/", latCells, ",", lng+1, "/", lngCells)
            currentCell = hashTable[lat, lng]
            for amenityType in amenitiesList:
                # No locations of this type
                if not currentCell[amenitiesIndices[amenityType]]:
                    continue

                cellCoords = cityCoords[lat, lng]
                # Iterate all the objects in this cell and type

                for location in filter(lambda x:
                                           x[0] >= cellCoords[0]
                                       and x[0] < cellCoords[0] + latStep
                                       and x[1] >= cellCoords[1]
                                       and x[1] < cellCoords[1] + lngStep,
                                       currentCell[amenitiesIndices[amenityType]]):
                    localPatterns = defaultdict(lambda: 0)
                    # retrieve unique patterns for current object
                    # then move unique patterns to global pattern storage (cliquePatterns)

                    # this is D array from article "multiway spatial join" by mamoulis
                    newDict = dict()

                    for neighborAmenityType in filter(lambda x: currentCell[amenitiesIndices[x]]
                                                      and x != amenityType,amenitiesList):
                        cur_locations = list([])
                        for neighborlocationIndex in range(len(currentCell[amenitiesIndices[neighborAmenityType]])):
                            neighborlocation = currentCell[amenitiesIndices[neighborAmenityType]][neighborlocationIndex]
                            if neighborlocation[0] - location[0] < -lngEps:
                                continue
                            if location[0] - neighborlocation[0] > lngEps:
                                break
                            if hlp.checkDist(location, neighborlocation, 50):
                                cur_locations.append(neighborlocation)
                        if len(cur_locations) > 0:
                            newDict[neighborAmenityType] = cur_locations

                    while len(newDict) > 0:
                        #if amenityType == 'dentist':
                         #   print('dentist',newDict)
                        for next_atype, next_list in newDict.items():
                            del newDict[next_atype]
                            processSet(next_atype, next_list, newDict, [amenityType], localPatterns, thresh, [(amenityType, location)],0)
                            break
                    # now for current object move every unique pattern to global storage
                    for pat, val in localPatterns.items():
                        patterns[amenityType][pat] += 1
    print('Mining algorithm took', time()-start, 'to execute')
    return time()-start, patterns

# Algorithm 1 : Start Patterns
cities, amenitiesIndices, amenitiesList = hlp.loadCities("../amenities_list.json", "../cities/", "ProvidenceNew.csv")
start = time()
data = cities['ProvidenceNew']

minLat, minLng, maxLat, maxLng = data.location_lat.min(), data.location_lng.min(), data.location_lat.max(), data.location_lng.max()
lowerLeft = minLat, minLng
upperRight = maxLat, maxLng
relPoint = gp.Point(minLat, minLng)

cityCoords, hashTable, lngEps, latEps = hlp.initializeContainers(minLat, minLng, maxLat, maxLng, amenitiesList)

latCells, lngCells, _ = cityCoords.shape
latStep = (maxLat - minLat)/latCells
lngStep = (maxLng - minLng)/lngCells

hashTable, hasingTime = hashData(hashTable, data, latCells, lngCells, latStep, lngStep, lngEps, latEps)
#miningTime, patterns = mineStarPatterns(hashTable, latCells, lngCells, latStep, lngStep, lngEps)
miningTime, patterns = mineCliquePatterns(hashTable, latCells, lngCells, latStep, lngStep, lngEps)
#print(patterns)
#print(len(patterns))

sortedAmenities = {}
for amenityType, locations in data.groupby('type_lowest'):
    sortedAmenities[amenityType] = list(zip(locations.location_lat.tolist(),
                                            locations.location_lng.tolist(),
                                           locations.type_lowest.tolist()))
    sortedAmenities[amenityType].sort(key = lambda x : x[0])
amenityLocations = [(key, value) for (key, value) in sortedAmenities.items()]
amenityLocations.sort(key = lambda x: x[0])

countAmenities = {}
for atype, alist in amenityLocations:
    countAmenities[atype] = len(alist)

    #calculate amount of objects of each type

#for each type get all patterns and for each pattern (via dictionary) that is not banned
#   -> calculate pr=supp/tot_obj
#if newly calculated is smaller than existing for existing pattern - replace minimum
#if it is smaller than threshold - then ban the pattern and do not check it elsewhere

#print all patterns that have not been benned, as well as their pr value.

pr = {}
thresh = 0.05

for amenityType, amenityPats in patterns.items():
    for aPat, aPatCount in amenityPats.items():
        newVal = aPatCount/countAmenities[amenityType]
        try:
            curVal = pr[aPat]
            if curVal != -1:
                if newVal < thresh:
                    pr[aPat] = -1
                else:
                    if newVal < curVal:
                        pr[aPat] = newVal
        except KeyError:
            if newVal < thresh:
                pr[aPat] = -1
            else:
                pr[aPat] = newVal
pr_clean = [(apat, apr) for apat, apr in pr.items() if apr > 0]

pd.DataFrame(pr_clean, columns=['pattern','prev']).to_csv('prevalentPatternsProvidence.csv', index=None)

print('Total algorithm time took', time()-start, 'to execute')
print("Number of patterns: ",len(pr_clean))