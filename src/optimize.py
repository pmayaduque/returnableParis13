# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 10:02:22 2023

@author: pablo.maya
"""
import gurobipy as gp
from gurobipy import GRB
from utilities import expand_data
from classes import Solution
import pandas as pd
import numpy as np
import re



def create_model(instance):
    
    # # # desagregate data
    
    # # c_buy: buying cost
    # # c_clasif: cost of classigying at collection center
    # # c_activ: collection center activation cost
    # # c_hold: cost of holding aty the collection center
    # # capC: classification capacity
    # # capS: sortage capacity
    # # inisS: initial stock at the collection center
    # collectors, c_buy, c_clasif, c_activ, c_hold, capC, capS, iniS  = gp.multidict(data['collectors'])
    
    # # c_clean: cost of cleaning at transformer
    # # capM: casssification capacity
    # manufs, c_clean, capM  = gp.multidict(data['manufs'])

    # regions = data['regions']
    # producers = data['producers']
    # time = data['time']
    
    # # Sparse network
    # # echelon 1 (regions to collections centers)
    # arcs_e1 = gp.tuplelist(data['arcs_e1'])

    # # echelon 2 (collection centers to manufacturers)
    # arcs_e2, cost_e2 = gp.multidict(data['arcs_e2'])

    # # echelon 3 (manufaturers to producers)
    # arcs_e3, cost_e3 = gp.multidict(data['arcs_e3'])


    # # 2.5 generation and demands
    # # generation in each region
    # gen = data['gen']
    # demP = data['demP']
    # dt = data['dt']
    # capV = data['capV']
    
    # regions, collectors, manufs, producers, time, c_buy, c_clasif, \
    #     c_activ, c_hold, capC, capS, iniS, c_clean, capM, arcs_e1, arcs_e2, \
    #     arcs_e3, cost_e2,  cost_e3, gen, demP, dt, capV  = expand_data(data)
    
    regions = instance.regions
    collectors = instance.collectors
    manufs = instance.manufs
    producers= instance.producers
    time= instance.time
    c_buy= instance.c_buy
    c_clasif = instance.c_clasif
    c_activ = instance.c_activ
    c_hold = instance.c_hold
    capC = instance.capC
    capS = instance.capS
    iniS = instance.iniS 
    c_clean = instance.c_clean
    capM = instance.capM
    arcs = instance.arcs
    c_transp = instance.c_transp
    gen = instance.gen
    demP= instance.demP
    dt = instance.dt
    capV  = instance.capV
    
    model = gp.Model('returnability')
    
    # 3.2. create variables
    flow = model.addVars(arcs, time,  name="flow")
    activ = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ")
    activ_f = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ_f")
    stock = model.addVars(collectors, time, name="stock")
    trips = model.addVars(arcs, time,  vtype=gp.GRB.INTEGER, name="trip")
    
    # # 3.3. create the objective function
    obj = gp.LinExpr()
    # buying and classification cost
    for r,c,t in flow:
        if r in regions and c in collectors:
            obj += c_buy[c]*flow[r,c,t] + c_clasif[c]*flow[r,c,t]
        
    # transforming (cleaning all income bottles)
    for c,m,t in flow:
        if c in collectors and m in manufs:
            obj += c_clean[m]*flow[c,m,t] 
    
    # collection center activation cost and inventory holding
    for c,t in [(c,t) for c in collectors for t in time]:
        obj += c_activ[c]*activ[c,t] + c_hold[c]*stock[c,t]
    
    # transport from collections to transformers
    for c,m,t in flow:
        if c in collectors and m in manufs:
            obj += c_transp[c,m]*trips[c,m,t]
        
    
    # transport from transformers to producers 
    for m,p,t in flow:
        if m in manufs and p in producers:
            obj += c_transp[m,p]*trips[m,p,t]
        
    # set the objective 
    model.setObjective(obj, GRB.MINIMIZE)
    
    # 3.4. Constraints
    
    # classification capacity
    constr_capC = model.addConstrs(
        (flow.sum('*', c, t) <= capC[c]*activ[c,t] for c in collectors for t in time), "capC")
    
    # generation at each region
    constr_gen = model.addConstrs(
        (flow.sum(r, '*', t) <= gen[r,t]  for r in regions for t in time), "gen")
    
    # storage capacity
    constr_capS = model.addConstrs(
        (stock[c,t]<=capS[c] for c in collectors for t in time), "capS")
    
    # transformer capacity
    constr_capM = model.addConstrs(
        (flow.sum('*', m, t) <= capM[m] for m in manufs for t in time), "capM")
    
    # stock balance
    def prev_stock(c,t):
        if t <= 1:
            return iniS[c]
        return stock[c,t-1]
        
    cosntr_stock = model.addConstrs(
        (stock[c,t] == prev_stock(c,t) + flow.sum('*', c, t) - flow.sum(c,'*', t) for c in collectors for t in time), "stock")
    
    
    # demand fulfillment
    constr_demP = model.addConstrs(
        (flow.sum('*',p, t) >= demP[p,t] for p in producers for t in time), "demP")
    
    # commercial relationship
    constr_relat1 = model.addConstrs(
        (activ[c,t] >= activ_f[c,t1] for c in collectors for t1 in time for t in range(t1, min(t1+dt, len(time)))), "relat1")
    
    def prev_actv(c, t):
        if t <=1:
            return 0
        return activ[c,t-1]    
    constr_relat2 = model.addConstrs(
        (activ_f[c,t]>=activ[c,t] - prev_actv(c, t) for c in collectors for t in time), "relat2"
        )
    
    # balance at transformers
    constr_manuf_bal = model.addConstrs(
        (flow.sum('*', m, t) == flow.sum(m, '*', t) for m in manufs for t in time), "manuf_balanc"
        )
    
    # round up trips
    constr_trips_e2 = model.addConstrs(
        (trips[c,m,t] >=flow[c,m,t]/capV for c in collectors for m in manufs for t in time), "trips_e2"
        )
    
    # round up trips
    constr_trips_e3 = model.addConstrs(
        (trips[m,p,t] >= flow[m,p,t] / capV for m in manufs for p in producers for t in time), "trips_e3"
        )
    
    model.update()
    
    return model

def solve_model(model):
    # optimize the model
    model.optimize()
    
    return model

def get_results(model, instance):

    # get solution
    if model.Status == GRB.OPTIMAL:
        # dataframes with variables
        flows = []
        network = []
        for var in model.getVars():
            row = []    
            row.append(var.VarName.split('[')[0])
            indexes = re.findall(r'\[(.*?)\]', var.VarName)[0].split(',')
            #indexes = re.findall(r'\d', var.VarName.split('[')[1])
            [row.append(index) for index in indexes]
            row.append(var.X)
            if any(name in var.VarName for name in ['flow', 'trip']):
                flows.append(row)
            else:
                network.append(row)
        # Create data frames with the solution
        df_flows = pd.DataFrame.from_records(flows, columns=['name', 'origin', 'destination', 'period', 'value'])
        df_flows['arc'] = list(zip(df_flows['origin'], df_flows['destination']))
        df_network = pd.DataFrame.from_records(network, columns=['name', 'facility', 'period', 'value'])
        

        df_flows_o = df_flows[df_flows['name']=='flow']
        # calculated transport cost       
        df_flows_o['trips'] = np.ceil((df_flows_o['value']-0.001)/instance.capV)
        df_flows_o['c_transp'] = df_flows_o['arc'].map(instance.c_transp)*df_flows_o['trips']
        c_transp = df_flows_o['c_transp'].sum()      
        c_transp_e2 = df_flows_o[df_flows_o['origin'].isin(instance.collectors)]['c_transp'].sum()
        c_transp_e3 = df_flows_o[df_flows_o['origin'].isin(instance.manufs)]['c_transp'].sum()
        # cost of buying and classif
        df_collect = df_flows[df_flows['destination'].isin(instance.collectors)].groupby(['destination'], as_index= False).agg(total = ('value', sum))
        df_collect['c_buy'] = df_collect['destination'].map(instance.c_buy)*df_collect['total']
        df_collect['c_clasif'] = df_collect['destination'].map(instance.c_clasif)*df_collect['total']
        c_buy = df_collect['c_buy'].sum()
        c_clasif = df_collect['c_clasif'].sum()
        # cost of cleaning all incoming bottles
        df_clean = df_flows_o[df_flows_o['destination'].isin(instance.manufs)].groupby(['destination'], as_index= False).agg(total = ('value', sum))
        df_clean['c_clean'] = df_clean['destination'].map(instance.c_clean)*df_clean['total']
        c_clean = df_clean['c_clean'].sum()
        # cost of activiting facilities
        df_actv = df_network[df_network['name']=='activ'].groupby(['facility'], as_index=False).agg(count = ('value', sum))
        df_actv['c_activ'] = df_actv['facility'].map(instance.c_activ)*df_actv['count']
        c_activ = df_actv['c_activ'].sum()
        # cost of holding
        df_stock = df_network[df_network['name']=='stock'].groupby(['facility'], as_index=False).agg(count = ('value', sum))
        df_stock['c_hold'] = df_stock['facility'].map(instance.c_hold)*df_stock['count']
        c_hold = df_stock['c_hold'].sum()
        
       
        # dictionary summarising results
        dict_sol ={
            'obj_val': model.ObjVal,
            'runTime': model.Runtime,
            'gap': model.MIPGap,
            'c_transp': c_transp,
            'c_transp_e2': c_transp_e2,
            'c_transp_e3': c_transp_e3, 
            'c_total':   c_transp + c_buy + c_clasif + c_clean + c_activ + c_hold, 
            'q_buy': dict(zip(df_collect['destination'], df_collect['total'])),
            'c_buy': c_buy,
            'c_clasif': c_clasif,
            'q_clean': dict(zip(df_clean['destination'], df_clean['total'])),
            'c_clean': c_clean,
            'q_activ': dict(zip(df_actv['facility'], df_actv['count'])),
            'c_activ': c_activ}
    
        
        # create solution object
        solution = Solution(instance, dict_sol, df_flows, df_network)
        return "Optimal", solution
    else:
        return "non-optimal", None