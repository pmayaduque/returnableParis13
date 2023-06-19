# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 10:02:22 2023

@author: pablo.maya
"""
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import re

def create_model(data):
    
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

    regions = data['regions']
    producers = data['producers']
    time = data['time']
    
    # Sparse network
    # echelon 1 (regions to collections centers)
    arcs_e1 = gp.tuplelist(data['arcs_e1'])

    # echelon 2 (collection centers to manufacturers)
    arcs_e2, cost_e2 = gp.multidict(data['arcs_e2'])

    # echelon 3 (manufaturers to producers)
    arcs_e3, cost_e3 = gp.multidict(data['arcs_e3'])


    # 2.5 generation and demands
    # generation in each region
    gen = data['gen']
    demP = data['demP']
    dt = data['dt']
    capV = data['capV']

    
    
    model = gp.Model('returnability')
    
    # 3.2. create variables
    flow_e1 = model.addVars(arcs_e1, time,  name="flow_e1")
    flow_e2 = model.addVars(arcs_e2, time,  name="flow_e2")
    flow_e3 = model.addVars(arcs_e3, time,  name="flow_e3")
    activ = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ")
    activ_f = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ_f")
    stock = model.addVars(collectors, time, name="stock")
    trips_e2 = model.addVars(arcs_e2, time,  vtype=gp.GRB.INTEGER, name="trips_e2")
    trips_e3 = model.addVars(arcs_e3, time,  vtype=gp.GRB.INTEGER, name="trips_e3")
    
    # 3.3. create the objective function
    obj = gp.LinExpr()
    # buying and classification cost
    for r,c,t in flow_e1:
        obj += c_buy[c]*flow_e1[r,c,t] + c_clasif[c]*flow_e1[r,c,t]
        
    # transforming (cleaning)
    for m,p,t in flow_e3:
        obj += c_clean[m]*flow_e3[m,p,t] 
    
    # collection center activation cost and inventory holding
    for c,t in [(c,t) for c in collectors for t in time]:
        obj += c_activ[c]*activ[c,t] + c_hold[c]*stock[c,t]
    
    # transport from collections to transformers
    for c,m,t in flow_e2:
        obj += cost_e2[c,m]*trips_e2[c,m,t]
        
    
    # transport from transformers to producers 
    for m,p,t in flow_e3:
        obj += cost_e3[m,p]*trips_e3[m,p,t]
        
    # set the objective 
    model.setObjective(obj, GRB.MINIMIZE)
    
    # 3.4. Constraints
    
    # classification capacity
    constr_capC = model.addConstrs(
        (flow_e1.sum('*', c, t) <= capC[c]*activ[c,t] for c in collectors for t in time), "capC")
    
    # generation at each region
    constr_gen = model.addConstrs(
        (flow_e1.sum(r, '*', t) <= gen[r,t]  for r in regions for t in time), "gen")
    
    # storage capacity
    constr_capS = model.addConstrs(
        (stock[c,t]<=capS[c] for c in collectors for t in time), "capS")
    
    # transformer capacity
    constr_capM = model.addConstrs(
        (flow_e2.sum('*', m, t) <= capM[m] for m in manufs for t in time), "capM")
    
    # stock balance
    def prev_stock(c,t):
        if t <= 1:
            return iniS[c]
        return stock[c,t]
        
    cosntr_stock = model.addConstrs(
        (stock[c,t] == prev_stock(c,t) + flow_e1.sum('*', c, t) - flow_e2.sum(c,'*', t) for c in collectors for t in time), "stock")
    
    
    # demand fulfillment
    constr_demP = model.addConstrs(
        (flow_e3.sum('*',p, t) >= demP[p,t] for p in producers for t in time), "demP")
    
    # commercial relationship
    constr_relat1 = model.addConstrs(
        (activ[c,t] >= activ_f[c,t1] for c in collectors for t1 in time for t in range(t1, min(t1+dt, len(time)))))
    
    def prev_actv(c, t):
        if t <=1:
            return 0
        return activ[c,t-1]    
    constr_relat2 = model.addConstrs(
        (activ_f[c,t]>=activ[c,t] - prev_actv(c, t) for c in collectors for t in time), "relat2"
        )
    
    constr_manu_bal = model.addConstrs(
        (flow_e2.sum('*', m, t) == flow_e3.sum(m, '*', t) for m in manufs for t in time), "relat1"
        )
    
    # round up trips
    constr_trips_e2 = model.addConstrs(
        (trips_e2[c,m,t] >=3 for c in collectors for m in manufs for t in time), "trips_e2"
        )
    
    # round up trips
    constr_trips_e3 = model.addConstrs(
        (trips_e3[m,p,t] >= flow_e3[m,p,t] / capV for m in manufs for p in producers for t in time), "trips_e3"
        )
    
    
    return model

def solve_model(model):
    # optimize the model
    model.optimize()

    # get solution
    if model.Status == GRB.OPTIMAL:
        flows = []
        network = []
        for var in model.getVars():
            row = []    
            row.append(var.VarName.split('[')[0])
            indexes = re.findall(r'\[(.*?)\]', var.VarName)[0].split(',')
            #indexes = re.findall(r'\d', var.VarName.split('[')[1])
            [row.append(index) for index in indexes]
            row.append(var.X)
            if any(name in var.VarName for name in ['flow_e1', 'flow_e2', 'flow_e3', 'trips_e2', 'trips_e3']):
                flows.append(row)
            else:
                network.append(row)
        # Create data frames with the solution
        flow_vars = pd.DataFrame.from_records(flows, columns=['name', 'origin', 'destination', 'period', 'value'])
        nd_vars = pd.DataFrame.from_records(network, columns=['name', 'facility', 'period', 'value'])
        return "Optimal", flow_vars,  nd_vars
    else:
        return "non-optimal", None, None