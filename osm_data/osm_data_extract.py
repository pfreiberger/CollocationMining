# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 11:56:43 2017

@author: Philipp
"""

import requests
import lxml.etree as le
import pandas as pd
import os

def extract():
    min_lat = 55.6650
    width = 0.01
    height = 0.01
    
    while min_lat < 55.6950:
        min_long = 12.56
        while min_long < 12.6100:
            
            res = requests.get("https://www.openstreetmap.org/api/0.6/map?bbox={}%2C{}%2C{}%2C{}".format(
                min_long, min_lat, min_long+width, min_lat+height))
            min_long += width
            
            with open("{}_{}.osm".format(min_long,min_lat), "w", encoding='utf-8') as file:
                file.write(res.text)
            
        min_lat = round(min_lat+height, 3)

    
def clean(fname):    
    with open(fname,'r', encoding="utf-8") as f:
        doc=le.parse(f)
        for elem in doc.findall("node"):
            tags = elem.findall("tag")
            is_amenity = False
            for tag in tags:
                if tag.attrib['k']=='amenity':
                    is_amenity = True
                    break
            if not is_amenity:
                elem.getparent().remove(elem) 
        
        for elem in doc.findall("way"):
            elem.getparent().remove(elem)
            
        for elem in doc.findall("relation"):
            elem.getparent().remove(elem)
            
    return doc
    #with open("new_test.osm", "w") as f:
     #   f.write(le.tostring(doc).decode("utf-8"))
        
def to_df(xml_doc):
    rows = []
    for elem in xml_doc.findall("node"):
        long = elem.attrib["lon"]
        lat = elem.attrib["lat"]
        wc=None
        for tag in elem.findall("tag"):
            
            if tag.attrib["k"]=='amenity':
                amenity = tag.attrib["v"]
            
            elif tag.attrib["k"]=="wheelchair":
                wc = tag.attrib["v"]
        rows.append({"longitude": long, "latitude": lat, "type": amenity, "wheelchair": wc})
        
    
    return pd.DataFrame(rows, columns=["longitude", "latitude", "type", "wheelchair"])


frames = []
for fname in os.listdir("./"):
    if fname.endswith(".osm"): 
        # print(os.path.join(directory, filename))        
        doc = clean(fname)
        frames.append(to_df(doc))       

df = pd.concat(frames)
df.to_csv("amenities.csv", sep=',', encoding='utf-8')


    