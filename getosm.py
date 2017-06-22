# -*- coding: utf-8 -*-
"""
Created on Tue May 23 20:44:41 2017

@author: Philipp
"""

import requests

url = "https://www.openstreetmap.org/api/0.6/map?bbox=12.4865%2C55.6185%2C12.6638%2C55.7248"

response = requests.get(url)

print(response.text[1:200])