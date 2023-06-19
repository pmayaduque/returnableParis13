# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 09:23:27 2023

@author: pablo.maya
"""

import json

# read dat from file
def read_data_json(file_path):
    # Read the JSON file
    with open(file_path, "r") as json_file:
        json_data = json.load(json_file)
    
    data = {
            'regions': json_data['regions'],
            'collectors': json_data['collectors'],
            'manufs': json_data['manufs'],
            'producers': json_data['producers'],
            'time': json_data['time'],
            'arcs_e1': [tuple(k) for k in json_data['arcs_e1']],
            'arcs_e2': {tuple(eval(k)): v for k,v in json_data['arcs_e2'].items()},
            'arcs_e3': {tuple(eval(k)): v for k,v in json_data['arcs_e3'].items()},
            'gen' : {(eval(k)): v for k,v in json_data['gen'].items()},
            'demP' : {tuple(eval(k)): v for k,v in json_data['demP'].items()},
            'dt': json_data['dt'],
            'capV': json_data['capV']
            }
    return data