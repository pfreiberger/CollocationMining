import math
import pandas as pd
import geopy

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

points = pd.read_csv("../cities/small.csv")
minlat = points['location_lat'].min()
minlng = points['location_lng'].min()
relPoint = geopy.Point(minlat, minlng)
new_points = []
for row in points.iterrows():
    x, y = getXYpos(relPoint, geopy.Point(row[1]['location_lat'],row[1]['location_lng']))
    new_row = {'x': x, 'y': y, 'atype': row[1]['type_lowest']}
    new_points.append(new_row)
pd.DataFrame(new_points).to_csv('../cities/small_xy.csv')