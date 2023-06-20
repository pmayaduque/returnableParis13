# 1. import the libraries
import gurobipy as gp
from gurobipy import GRB
from utilities import read_data_json
from optimize import create_model, solve_model, get_results
from classes import Instance, Solution
import re
import pandas as pd
import numpy as np


# 1. basic instance of data

# c_buy: buying cost
# c_clasif: cost of classigying at collection center
# c_activ: collection center activation cost
# c_hold: cost of holding aty the collection center
# capC: classification capacity
# capS: sortage capacity
# inisS: initial stock at the collection center
collectors = {'c1': [100, 10, 100, 1, 300, 900, 1],
              'c2': [90, 9, 100, 1, 250, 250, 1],
              'c3': [80, 8, 100, 1, 300, 600, 1]}


# c_clean: cost of cleaning at transformer
# capM: casssification capacity
manufs =    {'m1': [10, 900],
     'm2': [9, 750]}

regions = ['r1', 'r2']
producers = ['p1', 'p2', 'p3']
time = [1, 2, 3, 4]


# Sparse network
# echelon 1 (regions to collections centers)
arcs = {('r1', 'c1'): 0, 
        ('r1', 'c2'): 0,
        ('r1', 'c3'): 0,
        ('r2', 'c1'): 0, 
        ('r2', 'c2'): 0,
        ('r2', 'c3'): 0,
        ('c1', 'm1'):   100,
        ('c1', 'm2'):   90,
        ('c2', 'm1'):   80,
        ('c2', 'm2'):   15,
        ('c3', 'm1'):   35,
        ('c3', 'm2'):   28,
        ('m1', 'p1'):   100,
        ('m1', 'p2'):   90,
        ('m1', 'p3'):   80,
        ('m2', 'p1'):   100,
        ('m2', 'p2'):   90,
        ('m2', 'p3'):   80}

# generation in each region
gen = {('r1', 1): 500,
       ('r1', 2): 500,
       ('r1', 3): 500,
       ('r1', 4): 500,
       ('r2', 1): 300,
       ('r2', 2): 300,
       ('r2', 3): 300,
       ('r2', 4): 300,
    }

# demand for each producer
demP = {('p1',1): 300,
        ('p1',2): 300,
        ('p1',3): 300,
        ('p1',4): 300,
        ('p2',1): 250,        
        ('p2',2): 250,        
        ('p2',3): 250,
        ('p2',4): 250,
        ('p3',1): 100,
        ('p3',2): 100,
        ('p3',3): 100,
        ('p3',4): 100}

# commercial relationship min duration
dt = 2
# vehicle capacity
capV = 100


# group data into a dictionary
data = {
        'regions': regions,
        'collectors': collectors,
        'manufs': manufs,
        'producers': producers,
        'time': time,
        'arcs': arcs,
        'gen': gen,
        'demP': demP,
        'dt': dt,
        'capV':capV
        }


# 2. create instance from data entered manually
instance = Instance(data)
model = create_model(instance)

# # Run de model from a json file in /data dolder
# data_json = read_data_json(r'../data/data.json') 
# instance = Instance(data_json)  
# model = create_model(instance)

# 3. solve model and get results
solve_model(model)
status, solution = get_results(model, instance)

# # 4. Check solution
validation = solution.solution_checker()



# # add arc column to df_flows
# df_flows = solution.df_flows
# df_flows['arc'] = list(zip(df_flows['origin'], df_flows['destination']))
# collectors, c_buy, c_clasif, c_activ, c_hold, capC, capS, iniS  = gp.multidict(data['collectors'])
# c_transp = {**{arc:0 for arc in arcs_e1}, **arcs_e2, **arcs_e3}

# #df_flows_agg = df_flows.groupby(['arc'], as_index=False).agg(
#     #total_flow = ('value', sum))
# # create a dataframe with the costs of flow in each arc

# # # agregated transportation costs in a single dataframe
# # df_arcs_e1 = pd.DataFrame.from_records(
# #     list(zip(data['arcs_e1'], np.zeros(len(data['arcs_e1'])))),
# #     columns = ['arc', 'c_transp'])
# # df_arcs_e2 = pd.DataFrame.from_dict(data['arcs_e2'], orient = 'index', columns =['c_transp'])
# # df_arcs_e3 = pd.DataFrame.from_dict(data['arcs_e3'], orient = 'index', columns =['c_transp'])
# # df_c_transp = pd.concat([df_arcs_e2, df_arcs_e3])
# # df_c_transp.reset_index(inplace=True)
# # df_c_transp.rename(columns={'index': 'arc'}, inplace=True)
# # df_c_transp = pd.concat([df_arcs_e1, df_c_transp])

# # # merge to flow_cost
# # df_flow_cost = pd.merge(df_flows, df_c_transp, on='arc', how='outer')

# collectors, c_buy, c_clasif, c_activ, c_hold, capC, capS, iniS  = gp.multidict(data['collectors'])
# c_transp = {**{arc:0 for arc in arcs_e1}, **arcs_e2, **arcs_e3}
# df_flows['c_transport'] = df_flows['arc'].map(c_transp)
# df_flows['c_buy'] = df_flows['destination'].map(c_buy)


# # # Run de model from a json file in /data dolder
# # data_json = read_data_json(r'../data/data.json')   
# # model = create_model(data_json)




    
# # flow_e1 = model.addVars(arcs_e1, time,  name="flow_e1")
# # flow_e2 = model.addVars(arcs_e2, time,  name="flow_e2")
# # flow_e3 = model.addVars(arcs_e3, time,  name="flow_e3")
# # activ = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ")
# # activ_f = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ_f")
# # stock = model.addVars(collectors, time, name="stock")
# # trips_e2 = model.addVars(arcs_e2, time,  vtype=gp.GRB.INTEGER, name="trips_e2")
# # trips_e3 

# # # 4. Print solution
# # if model.Status == GRB.OPTIMAL:
# #     # facility activation
# #     activ_f_sol = model.getAttr('X', model.activ_f)
# #     for c in collectors:
# #         for t in time:
# #             if activ_f_sol[c,t] > 0:
# #                 print('activ_f(%s,  %s): %g' % (c, t, activ_f_sol[c,t]))
# #     activ_sol = model.getAttr('X', model.activ)
# #     for c in collectors:
# #         for t in time:
# #             if activ_sol[c,t] > 0:
# #                 print('activ(%s,  %s): %g' % (c, t, activ_sol[c,t]))
# #     # flows from regions to collections
# #     print("Flow from regions to colllectors")
# #     flow_e1_sol = model.getAttr('X', model.flow_e1)
# #     for r,c,t in model.flow_e1:
# #         if flow_e1_sol[r,c,t]> 0:
# #             print('flow_e1(%s,  %s, %s): %g' % (r, c, t, flow_e1_sol[r,c,t])) 
# #     print("Flow collectors to transformers")
# #     flow_e2_sol = model.getAttr('X', model.flow_e2)
# #     for c,m,t in model.flow_e2:
# #         if flow_e2_sol[c,m,t]> 0:
# #             print('flow_e2(%s,  %s, %s): %g' % (c,m,t, flow_e2_sol[c,m,t])) 
# #     print("Flow transformers to producers")
# #     flow_e3_sol = model.getAttr('X', model.flow_e3)
# #     for m,p,t in model.flow_e3:
# #         if flow_e3_sol[m,p,t]> 0:
# #             print('flow_e3(%s,  %s, %s): %g' % (m,p,t, flow_e3_sol[m,p,t])) 
# #     print("Trips collectors  to transformers")
# #     trips_e2_sol = model.getAttr('X', model.trips_e2)
# #     for c,m,t in model.trips_e2:
# #         if trips_e2_sol[c,m,t]> 0:
# #             print('trips_e2(%s,  %s, %s): %g' % (c,m,t, trips_e2_sol[c,m,t]))
# #     print("Trips transformers to producers")
# #     trips_e3_sol = model.getAttr('X', model.trips_e3)
# #     for m,p,t in model.trips_e3:
# #         if flow_e3_sol[m,p,t]> 0:
# #             print('trips_e3(%s,  %s, %s): %g' % (m,p,t, trips_e3_sol[m,p,t])) 

            

# # # model.update()
# # # constraint = constr_relat2['c3',2]
# # # constraint_expr = model.getRow(constraint)
# # # # Print the mathematical expression of the constraint
# # # sense = constraint.getAttr(gp.GRB.Attr.Sense)
# # # rhs = constraint.getAttr(gp.GRB.Attr.RHS)

# # # expr_str = f"{constraint_expr} {sense} {rhs}"
# # # print(expr_str)

