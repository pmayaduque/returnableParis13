# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 16:13:16 2023

@author: pablo.maya
"""

import gurobipy as gp
import numpy as np
import random
from utilities import create_partition, euclidean

class Instance:
  """
    Represents an instance of a mathematical optimization model.
    
    Args:
        data (dict): A dictionary containing the input data for the instance.
        name (str, optional): The name of the instance. Defaults to 'instance0'.
  """
  def __init__(self, data, name='instance0' ):

    
    self.name = name
    self.raw_data = data
    
    # desagregated data
    self.regions = data['regions']
    self.producers = data['producers']
    self.time = data['time']
    
    # desagregate data  
    
    # c_buy: buying cost
    # c_clasif: cost of classigying at collection center
    # c_activ: collection center activation cost
    # c_hold: cost of holding aty the collection center
    # capC: classification capacity
    # capS: sortage capacity
    # inisS: initial stock at the collection center
    self.collectors,  self.c_buy,  self.c_clasif,  self.c_activ,  self.c_hold, \
        self.capC,  self.capS,  self.iniS  =  gp.multidict(data['collectors'])
    
    # c_clean: cost of cleaning at transformer
    # capM: casssification capacity
    self.manufs, self.c_clean, self.capM  = gp.multidict(data['manufs'])

    # Sparse network
    self.arcs, self.c_transp = gp.multidict(data['arcs'])

    
    self.gen = data['gen'] # generation in each region at each period
    self.demP = data['demP'] # demand of each producer at each time
    self.dt = data['dt'] # number of periods for the collector agreement
    self.capV = data['capV'] # Vehicle capacity
    self.n_reg = data['n_reg'] # number of regions
    self.alpha = data['alpha'] # maximum difference in coverage among regions
    
  def __init__(self, name='instance0' ):
      self.name = name
      
      
  def instance_generator(self, n_reg, n_collec, n_manufs, n_prod, periods, demand_range, 
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
        
        self.regions = ["r"+str(i+1) for i in range(n_reg)]
        self.collectors = ["c"+str(i+1) for i in range(n_collec)]
        self.manufs = ["m"+str(i+1) for i in range(n_manufs)]
        self.producers = ["p"+str(i+1) for i in range(n_prod)]
        self.time = [(t+1) for t in range(periods)]
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
    
      
      

    
class Solution:
    """
    Represents a solution to a mathematical optimization model.
    
    Args:
        instance (object): An instance object containing the parameters used in the model.
        dict_sol (dict): A dictionary containing the solution results.
        df_flows (DataFrame): A DataFrame containing the flow variables of the solution.
        df_network (DataFrame): A DataFrame containing the network variables of the solution.
        name (str, optional): The name of the solution. Defaults to 'solution0'.
    """
    def __init__(self, instance, dict_sol, df_flows, df_network, name='solution0'):
        self.instance = instance
        self.dict_sol = dict_sol
        self.df_flows = df_flows
        # agregate a column arc to be used as a key
        self.df_flows['arc'] = list(zip(self.df_flows['origin'], self.df_flows['destination']))
        self.df_network = df_network
        
        
    def solution_checker(self):
        # function to compare a value in the df to a value in a dictionary with que (a1,a2)
        def check_condition(row, dictionary, key):
            if len(key)==1:
                return row['value'] <= dictionary[(row[key[0]], row[key[1]])]
            if len(key)==2:
                return row['value'] <= dictionary[(row[key[0]], row[key[1]])]
        
        # get only the flow variables 
        flows = self.df_flows[self.df_flows['name']=='flow']
        network = self.df_network
        
        # check objaective function
        if self.dict_sol['obj_val'] - self.dict_sol['c_total'] >= 0.1:
            return False
        
        # check number of regions covered
        n_reg = network[network['name']=='cover']['value'].sum()
        if np.abs(n_reg - self.instance.n_reg) > 0.1:
            return False
        
        # check the capacity at collection centers
        flow_c = flows[flows['destination'].isin(self.instance.collectors)]
        flow_c= flow_c.groupby(['destination', 'period'], as_index=False)['value'].sum()
        condition_mask = flow_c.apply(check_condition, 
                                      args = (self.instance.capC, ('destination')), axis=1)
        if not condition_mask.all():
            return False
        
        # check regions geneartion limits
        flow_r = flows[flows['origin'].isin(self.instance.regions)]
        flow_r = flow_r.groupby(['origin', 'period'], as_index=False)['value'].sum()
        condition_mask = flow_r.apply(check_condition, 
                                      args = (self.instance.gen, ('origin', 'period')), axis=1)
        if not condition_mask.all():
            return False

        # check stock capacity
        network_s = network[network['name']=='stock']
        network_s.reset_index(inplace=True)
        condition_mask = network_s.apply(check_condition, 
                                      args = (self.instance.capS, ('facility')), axis=1)
        if not condition_mask.all():
            return False
        
        # check the capacity at transformers
        flow_m = flows[flows['destination'].isin(self.instance.manufs)]
        flow_m= flow_m.groupby(['destination', 'period'], as_index=False)['value'].sum()
        condition_mask = flow_m.apply(check_condition, 
                                      args = (self.instance.capM, ('destination')), axis=1)
        if not condition_mask.all():
            return False
        
        # check the inventory
        flow_c_out = flows[flows['origin'].isin(self.instance.collectors)]
        flow_c_out= flow_c_out.groupby(['origin', 'period'], as_index=False)['value'].sum()
        
        a = 1
        for c in self.instance.collectors:
            for t in self.instance.time:
                stockLHS = list(network_s.loc[(network_s['facility'] == c) & (network_s['period'] == t), 'value'])[0]
                if t == 1:
                    stockRHS = list([self.instance.iniS[c]])[0]
                else:
                    stockRHS = list(network_s.loc[(network_s['facility'] == c) & (network_s['period'] == t-1), 'value'])[0]
                stockRHS += list(flow_c.loc[(flow_c['destination'] == c) & (flow_c['period'] == t), 'value'])[0]
                stockRHS -= list(flow_c_out.loc[(flow_c_out['origin'] == c) & (flow_c_out['period'] == t), 'value'])[0]
                if np.abs(stockLHS - stockRHS) > 0.1:
                    return False
  
        
        return True
        
