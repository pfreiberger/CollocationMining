# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:22:28 2017

@author: Philipp
"""

import pandas as pd
import json

def load_data():
    try:
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
        return data
    except Exception as e:
        raise
    
    

if __name__=="__main__":
    df = pd.DataFrame(patternInstances)
    grouped = df.groupby(['instanceid', 'pattern'])
    new_df = grouped.aggregate(lambda x: tuple(x))