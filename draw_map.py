# -*- coding: utf-8 -*-
"""
Created on Sat Jun 17 10:27:21 2017

@author: Philipp
"""

import gmplot
from itertools import cycle

def get_color(_type):
    color_dict = {
            "bar": "blue",
            "cafe": "red",
            "restaurant": "yellow",
            "default": "grey",
            "leisure": "green",
            "toilets": "white",
            "education": "black",
            "bicycle_parking": "cyan"}
    color="grey"
    if _type in color_dict.keys():
        color = color_dict[_type]
    
    return color

def get_marker(_type):
    color_dict = {
            "bar": "#0000FF",
            "cafe": "#FF0000",
            "restaurant": "#FFD700",
            "default": "#FFFFFF",
            "leisure": "#32CD32",
            "toilets": "#8B0000",
            "education": "#000000",
            "bicycle_parking": "#F08080"}
    color="grey"
    if _type in color_dict.keys():
        color = color_dict[_type]
    
    return color
    

def plot_pins(coords):
    gmap = gmplot.GoogleMapPlotter(55.677057, 12.589111, 14)
    for lat, long, amenity in coords:
        if True:#amenity != "bicycle_parking":
            color = get_color(amenity)
            gmap.circle(lat, long, 10, color, ew=2)
    
    gmap.draw("pin_map.html")
    
    
def plot_neighbours(dic):
    #colors = ["red", "yellow", "blue", "green", "cyan", "black", "grey"]
    gmap = gmplot.GoogleMapPlotter(55.677057, 12.589111, 14)
    
    #quickfix for windows
    gmap.coloricon = gmap.coloricon.replace("\\", "/")
    amenities=set()
    col = "FFFFFF"
    for k, cliques in dic.items():
        for clique in cliques:
            lats = [elem[0] for elem in clique]
            longs = [elem[1] for elem in clique]
        
            lats.append(clique[0][0])
            longs.append(clique[0][1])
        #for elem in v:
         #   lats = [elem[0]]
          #  longs = []
           # lats.extend([x[0] for x in elem[1]])
            #longs.extend([x[1] for x in elem[1]])
            #lats.append(elem[0][0])
            #longs.append(elem[0][1])#
      
            # only draw triples and more
            if len(lats) > 3:
                x = [elem[2] for elem in clique]
                x.sort()
                pattern = ".".join(x)
                if "bicycle_parking.cafe.restaurant"== pattern:
                    [amenities.add(elem) for elem in clique]
                     
                    
                    num = int(col, 16)
                   
                    col = hex(int(num-2038))
                    c = "#"+str(col).upper()[2:]
    
                    gmap.plot(lats, longs, color=c, edge_width=1)
                
    for amenity in amenities:
        color = get_color(amenity[2])
        gmap.marker(amenity[0], amenity[1], color=get_marker(amenity[2]), title=amenity[2])
        
        gmap.circle(amenity[0], amenity[1], 4, color, ew=0.3)
    gmap.draw("neighbour_map.html")
    print()
    
if __name__=="__main__":
    #lats = [55.6660178, 55.66569499999999,55.665664, 55.6660178]
    #longs  = [12.597706, 12.5976434, 12.597758, 12.597706]
    #plot_polygon(lats, longs)
    
    plot_neighbours(dic)
    
    #cities, amenitiesIndices, amenitiesList = hlp.load_city()
    #data = cities['Copenhagen']
    
    
    
    
    #coords = zip(data["latitude"], data["longitude"], data["type"])
    #plot_pins(coords)
    
