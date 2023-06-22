# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 16:13:16 2023

@author: pablo.maya
"""

import gurobipy as gp
import numpy as np

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
        
