#import numpy as np
from time import time
from collections import defaultdict
import math
from geopy.distance import VincentyDistance as vincenty
from geopy.location import Location
import geopy as gp
#import itertools
import helpers as hlp
import pandas as pd
import draw_map as dm

patternInstances = []


def hashData(hashTable, data, latCells, lngCells, latStep, lngStep, latEps, lngEps):
    global relPoint
    start = time()
    for index, location in data.iterrows():
        lat, lng = location.latitude, location.longitude
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
                    if hashTable[latId, lngId, amenitiesIndices[location.type]]:
                        hashTable[latId, lngId, amenitiesIndices[location.type]].append((lat, lng, x, y))
                        hashTable[latId, lngId, amenitiesIndices[location.type]].sort(key = lambda x : x[0])
                    else:
                        hashTable[latId, lngId, amenitiesIndices[location.type]] = [(lat, lng, x, y)]
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
        newid = len(patternInstances)
        #print("curid",newid)
        all_locations = [location]
        patternInstances.append({'latitude': location[0], 'longitude': location[1], 'type': cur_atype, 'pattern': subPattern, 'size': len(newPatList), 'instanceid': newid})
        #add new instance
        for objtuple in objectset:
            all_locations.append(objtuple[1])
            patternInstances.append({'latitude': objtuple[1][0], 'longitude': objtuple[1][1], 'type': objtuple[0], 'pattern': subPattern, 'size': len(newPatList), 'instanceid': newid})
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
    for lat in range(latCells):
        for lng in range(lngCells):
            print("Processing cell", lat+1, "/", latCells, ",", lng+1, "/", lngCells)
            currentCell = hashTable[lat, lng]
            for amenityType in amenitiesList:
                # No locations of this type in current cell
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
                    #print(amenityType)
                    #print(newDict)
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


    
def group_instances():
    
    df = pd.DataFrame(patternInstances, columns=["instanceid","latitude", "longitude", "pattern", "size", "type"])
    grouped = df.groupby(['instanceid'])
    return grouped.aggregate(lambda x: tuple(x))




def group_by_location(data):
    # distance between two points
    remove = [1972, 2001, 167, 172, 189, 28, 152, 196, 182, 224, 143, 218, 199, 213, 218, 534, 247, 502, 523, 492, 511, 531, 571, 572, 573, 575, 414, 505, 515, 516, 542, 511, 531, 501, 414, 517, 524, 549, 497, 545, 496, 503, 515, 517, 524, 538, 549, 569, 570, 574, 1285, 504, 583, 535, 497, 586, 650, 652, 651, 671, 650, 698, 659, 704, 687, 827, 835, 837, 825, 948, 1328, 866, 860, 954, 895, 1185, 1298, 1197, 1299, 1118, 1320, 1171, 1278, 1317, 1186, 1284, 1294, 1242, 1269, 1223, 1272, 1327, 1194, 954, 1262, 1252, 1343, 1366, 1374, 1403, 1377, 1403, 1521, 1519, 1521, 1798, 1571, 1827, 1728, 1840, 1881, 1898, 1786, 1890, 1841, 1824, 1730, 1745, 1822, 1766, 1848, 1817, 1802, 1880, 1863, 1816, 1880, 1872, 1900, 1824, 1907, 1847, 1847, 1870, 1905, 1870, 1883, 1901, 1904, 1571, 1827, 1730, 2000, 2034, 2218, 2202, 2224, 2299, 2299, 2224, 2305, 2312, 2336, 2384, 2380, 2381, 2380, 2448, 2476, 2480, 2551, 2449, 2472, 2475, 2478, 2487, 2490, 2479, 2481, 2484, 2485, 2486, 2479, 2485, 2488, 2489, 2448, 2474, 2475, 2480, 2482, 2481, 2483, 2484, 2486, 2491, 2494, 2488, 2489, 2491, 2494, 45, 1158, 230, 562, 510, 532, 514, 563, 555, 690, 676, 1587, 1226, 1240, 1228, 1305, 1306, 1329, 1325, 1537, 1545, 1803, 1888, 1876, 1908, 1926, 1902, 2031, 2326, 2327, 22, 31, 590, 1410, 934, 940, 955, 924, 1205, 1760, 1917, 2235, 1475, 1474, 1477, 1478, 1474, 1479, 191, 220, 284, 540, 553, 607, 1074, 1115, 915, 1166, 1097, 1310, 1230, 1314, 1315, 1074, 1310, 1569, 1687, 1600, 1849, 1867, 1732, 1969, 1732, 2461, 2460, 2546, 2606, 217, 69, 69, 86, 89, 92, 342, 93, 107, 110, 112, 112, 110, 121, 305, 313, 313, 316, 318, 323, 322, 323, 327, 332, 335, 337, 346, 353, 354, 349, 350, 342, 351, 360, 364, 377, 393, 396, 609, 611, 611, 625, 626, 756, 740, 753, 756, 763, 764, 766, 770, 773, 773, 775, 780, 969, 981, 983, 982, 986, 1005, 1005, 1014, 1019, 1026, 1422, 1424, 1442, 1451, 1616, 1621, 1634, 1640, 1637, 1658, 1666, 1670, 1698, 1699, 1858, 1703, 1751, 2127, 2057, 2063, 2064, 2085, 2089, 2148, 2086, 2092, 2147, 2127, 2173, 2174, 2175, 2157, 2256, 2257, 2374, 2531, 2388, 2515, 2541, 472, 481, 482, 483, 484, 472, 480, 481, 482, 475, 476, 477, 478, 479, 480, 481, 486, 488, 489, 490, 800, 807, 808, 810, 811, 812, 813, 810, 811, 812, 813, 1057, 1059, 1060, 1061, 1341, 1355, 1357, 1358, 1383, 1384, 1994, 1383, 1384, 1387, 1388, 1387, 1388, 1997, 1998, 1460, 1462, 1464, 1465, 1467, 1468, 1467, 1468, 1471, 1490, 1497, 1498, 1499, 1501, 1502, 1503, 1505, 1506, 1507, 1508, 1509, 1510, 1511, 1510, 1511, 1513, 1514, 1515, 1694, 1696, 1697, 1936, 1940, 1940, 1955, 1954, 1966, 1994, 1996, 2009, 2013, 2014, 2020, 2233, 2121, 2125, 2110, 2120, 2122, 2114, 2119, 2123, 2118, 2119, 2132, 2133, 2134, 2135, 2136, 2137, 2138, 2139, 2140, 2141, 2142, 2143, 2144, 2498, 2177, 2178, 2179, 2180, 2177, 2178, 2179, 2180, 2182, 2183, 2596, 2598, 2599, 2291, 2291, 2294, 2498, 2501, 2506, 2506, 2504, 2507, 2540, 2511, 2512, 2513, 2524, 2569, 2570, 2571, 2573, 2574, 2575, 2581, 2584, 2584, 2586, 2586, 2588, 2588, 2590, 2590, 2592, 2592, 2594, 2597, 2601, 2596, 2597, 2598, 2599, 2601, 132, 442, 444, 445, 447, 449, 450, 449, 450, 646, 647, 802, 804, 1131, 1132, 1133, 1131, 1132, 1133, 1136, 1361, 1362, 1484, 1772, 1775, 1777, 1778, 1976, 1977, 1980, 2289, 2414, 2415, 2417, 2578, 1379, 1390, 1391, 1392, 1398, 1401, 2427]
    data.drop(remove, inplace=True)
    
    #remove = []
    #for amenity in data["type"].unique():
        
      #  relevant = data[data["type"]==amenity]
       # for i, x in relevant.iterrows():
        #    for j, y in relevant.iterrows():
         #       if i!=j and i not in remove:
          #          if vincenty(x["location"], y["location"]).meters <= 15:
           #             remove.append(j)
                        
    #print(remove)
                        
    
        
    
if __name__=="__main__":
     # Algorithm 1 : Start Patterns
    cities, amenitiesIndices, amenitiesList = hlp.load_city()
    start = time()
    data = cities['Copenhagen']
    group_by_location(data)
    
    # bounding box coordinates
    minLat, minLng, maxLat, maxLng = data.latitude.min(), data.longitude.min(), data.latitude.max(), data.longitude.max()
    lowerLeft = minLat, minLng
    upperRight = maxLat, maxLng
    relPoint = gp.Point(minLat, minLng)
    
    cityCoords, hashTable, lngEps, latEps = hlp.initializeContainers(minLat, minLng, maxLat, maxLng, amenitiesList)
    
    latCells, lngCells, _ = cityCoords.shape
    latStep = (maxLat - minLat)/latCells
    lngStep = (maxLng - minLng)/lngCells
    
    hashTable, hasingTime = hashData(hashTable, data, latCells, lngCells, latStep, lngStep, lngEps, latEps)
    #miningTime2, patterns2 = mineStarPatterns(hashTable, latCells, lngCells, latStep, lngStep, lngEps)
    miningTime, patterns = mineCliquePatterns(hashTable, latCells, lngCells, latStep, lngStep, lngEps)
    #print(patterns)
    #print(len(patterns))
    
    sortedAmenities = {}
    for amenityType, locations in data.groupby('type'):
        sortedAmenities[amenityType] = list(zip(locations.latitude.tolist(),
                                                locations.longitude.tolist(),
                                               locations.type.tolist()))
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
   
    
    df = pd.DataFrame(pr_clean, columns=['pattern','prev'])
    df.to_csv('prevalentPatternsProvidence.csv', index=None)
    
    print('Total algorithm time took', time()-start, 'to execute')
    print("Number of patterns: ",len(pr_clean))
    
    #sig_patterns = df[df[""]>0.1]
    
    new_df = group_instances() 
    pts = list(df["pattern"])
    
    dic = {}
    for index, row in new_df.iterrows():
        size = row['size'][0]
        key = row["pattern"][0].split(".")[0]
        if row["pattern"][0] in pts:
            elems=[]
            for i in range(size):   
                elems.append((row["latitude"][i], row["longitude"][i], row["type"][i]))
                
            try:
                dic[key].append(elems)
            except KeyError:
                dic[key] = [elems]
    
    dm.plot_neighbours(dic)