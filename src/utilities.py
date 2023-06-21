# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 09:23:27 2023

@author: pablo.maya
"""
import gurobipy as gp
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
            'arcs': {tuple(eval(k)): v for k,v in json_data['arcs'].items()},
            'gen' : {(eval(k)): v for k,v in json_data['gen'].items()},
            'demP' : {tuple(eval(k)): v for k,v in json_data['demP'].items()},
            'dt': json_data['dt'],
            'capV': json_data['capV'],
            'n_reg':json_data['n_reg'],
            'alpha':json_data['alpha']
            }
    return data

def expand_data(data):
    
    regions = data['regions']
    producers = data['producers']
    time = data['time']
    
    # desagregate data    
    # c_buy: buying cost
    # c_clasif: cost of classigying at collection center
    # c_activ: collection center activation cost
    # c_hold: cost of holding aty the collection center
    # capC: classification capacity
    # capS: sortage capacity
    # inisS: initial stock at the collection center
    collectors, c_buy, c_clasif, c_activ, c_hold, capC, capS, iniS  = gp.multidict(data['collectors'])
    
    # c_clean: cost of cleaning at transformer
    # capM: casssification capacity
    manufs, c_clean, capM  = gp.multidict(data['manufs'])

   
    # Sparse network
    # echelon 1 (regions to collections centers)
    arcs_e1 = gp.tuplelist(data['arcs_e1'])

    # echelon 2 (collection centers to manufacturers)
    arcs_e2, cost_e2 = gp.multidict(data['arcs_e2'])

    # echelon 3 (manufaturers to producers)
    arcs_e3, cost_e3 = gp.multidict(data['arcs_e3'])
    
    gen = data['gen']
    demP = data['demP']
    dt = data['dt']
    capV = data['capV']
    
    
    # data_e = {
    #     'regions' : data['regions'],
    #     'collectors': collectors,
    #     'manufs': manufs,
    #     'producers' : data['producers'],
    #     'time' : data['time'],
    #     'c_buy': c_buy,
    #     'c_clasif': c_clasif,
    #     'c_activ': c_activ, 
    #     'c_hold': c_hold, 
    #     'capC': capC, 
    #     'capS': capS, 
    #     'iniS': iniS,
    #     'c_clean': c_clean,
    #     'capM': capM,
    #     'arcs_e1': arcs_e1,
    #     'arcs_e2': arcs_e2, 
    #     'arcs_e3': arcs_e3,
    #     'cost_e2': cost_e2,        
    #     'cost_e3':arcs_e3        
    #     }
    return regions, collectors, manufs, producers, time, c_buy, c_clasif, \
        c_activ, c_hold, capC, capS, iniS, c_clean, capM, arcs_e1, arcs_e2, \
        arcs_e3, cost_e2,  cost_e3, gen, demP, dt, capV  

