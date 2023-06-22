# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 09:23:27 2023

@author: pablo.maya
"""

import json
import random
import numpy as np
from geopy.distance import geodesic as GD


def read_data_json(file_path):
    """
    Read data from a JSON file and return the extracted information as a dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary containing the extracted data from the JSON file.
    """
    # Open the JSON file for reading
    with open(file_path, "r") as json_file:
        json_data = json.load(json_file)

    # Extract required data from the loaded JSON
    data = {
        'regions': json_data['regions'],
        'collectors': json_data['collectors'],
        'manufs': json_data['manufs'],
        'producers': json_data['producers'],
        'time': json_data['time'],
        'arcs': {tuple(eval(k)): v for k, v in json_data['arcs'].items()},
        'gen': {eval(k): v for k, v in json_data['gen'].items()},
        'demP': {tuple(eval(k)): v for k, v in json_data['demP'].items()},
        'dt': json_data['dt'],
        'capV': json_data['capV'],
        'n_reg': json_data['n_reg'],
        'alpha': json_data['alpha']
    }
    
    return data

def create_partition(k, m, dev=0.25):
    numbers_list = []
    remaining_sum = m
    avg = m / k
    
    while True:        
        for _ in range(k - 1):
            deviation = random.uniform(-dev, dev)  # Random deviation from the mean
            number = int((1+ deviation)*avg) 
            numbers_list.append(number)
            remaining_sum -= number
        if  remaining_sum > 0:   
            remaining_sum = m - sum(numbers_list)
            numbers_list.append(remaining_sum)
            return numbers_list
        
        
def instance_generator(n_reg, n_collec, n_manufs, n_prod, periods, demand_range, 
                       p_capT, # percentage of increase of capacity regarding demand
                       p_capC, # percentage of increase of capacity regarding demand
                       p_capS, # perecentage of the capacity at collector
                       p_gen, # percentage of the generation considered in the demand 
                       v_base, # basis value of a returnable packaging
                       p_transp, # percenatje of transport per bootle 
                       d_tranp, # percentaje of variation accordin to distance [0, 1]
                       p_buy, # cost of buy as percentage of v_base of a packaging
                       p_clasif, # cost of classifying as percentage of v_base of a packaging
                       p_activ, # cost of activation as a percentaje of the value of the capacity
                       p_hold, # cost of stock as percentage of v_base of a packaging
                       p_clean, # cost of cleaning as percentage of v_base of a packaging
                       dt,
                       alpha,
                       min_reg):
    
    regions = ["r"+str(i+1) for i in range(n_reg)]
    collectors = ["c"+str(i+1) for i in range(n_collec)]
    manufs = ["m"+str(i+1) for i in range(n_manufs)]
    producers = ["p"+str(i+1) for i in range(n_prod)]
    time = [(t+1) for t in range(periods)]
    # create demands per region
    demP  = {(p,t):random.randint(demand_range[0], demand_range[1]) \
                for p in producers for t in time}
    
    # calculate the maximum demand in a period    
    agg_dem = {t: sum(val for (key, val) in demP.items() if key[1] == t) for t in set(key[1] for key in demP)}
    max_demt = max(list(agg_dem.values()))
    
    
    # create transformers capacity
    capT = create_partition(n_manufs, int(max_demt*(1+p_capT)))
    capT = {c:capT[i] for i, c in enumerate(manufs) }
    
    # create collectors clasif capacity, inventory capacity and initial value
    capC = create_partition(n_collec, int(max_demt*(1+p_capC)))
    capC = {c : capC[i] for i, c in enumerate(collectors) }
    capS = {k : int(v*p_capS) for k, v in capC.items()}
    iniS = {k : random.randint(0, v) for k, v in capS.items()}
    
    # create region generation
    gen = create_partition(n_collec, int(max_demt/p_gen))
    gen = {r : gen[i] for i, r in enumerate(regions) }
    
    # create vehicle capacity
    max_dem = max(demP.values())
    capV = random.randint(int(max_dem/2), max_dem)
    
    # Create arcs
    # create coordinates on a 100x100  panel
    nodes = {s:(random.uniform(0, 100), random.uniform(0, 100)) for s in collectors + manufs + producers}
    arcs_e1 = {(r, c):0 for r in regions for c in collectors}
    arcs_e2 = {(c, m):euclidean(nodes[c], nodes[m])  for c in collectors for m in manufs}
    arcs_e3 = {(m, p):euclidean(nodes[m], nodes[p])  for m in producers for p in producers}
    arcs = {**arcs_e1, **arcs_e2, **arcs_e3}
    max_dist = max(arcs.values())
    factor = d_tranp*capV*p_transp/max_dist
    arcs = {k : int(v*factor) for k,v in arcs.items()}
    
    c_buy = p_buy*v_base
    c_clasif = p_clasif*v_base
    c_activ = {c : capC[c]*v_base*p_activ for c in collectors}
    c_hold = p_hold*v_base
    c_clean = p_clean*v_base
    dt = dt
    alpha = alpha
    min_reg = min_reg
    
    return arcs, max_dist,  capV*p_transp


instance = instance_generator(4, 4, 4, 4, 4, (1000, 2000), 0.2, 0.3, 0.2, 0.3,\
                              100, 0.05, 1, 0.1, 0.05, 0.1, 0.01, 0.01, 3, 0.1, 3)
instance
    


def create_partition(k, m, dev=0.25):
    numbers_list = []
    remaining_sum = m
    avg = m / k
    
    while True:        
        for _ in range(k - 1):
            deviation = random.uniform(-dev, dev)  # Random deviation from the mean
            number = int((1+ deviation)*avg) 
            numbers_list.append(number)
            remaining_sum -= number
        if  remaining_sum > 0:   
            remaining_sum = m - sum(numbers_list)
            numbers_list.append(remaining_sum)
            return numbers_list

def euclidean(point1, point2):
    return np.sqrt((point1[0]-point2[0])**2 + (point1[0]-point2[0])**2)
    
    
create_partition(4, 100, 0.3)