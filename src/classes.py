# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 16:13:16 2023

@author: pablo.maya
"""

import gurobipy as gp


class Instance:
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


    
    self.gen = data['gen']
    self.demP = data['demP']
    self.dt = data['dt']
    self.capV = data['capV']
    self.n_reg = data['n_reg']
    self.alpha = data['alpha']
    
    
class Solution:
    def __init__(self, instance, dict_sol, df_flows, df_network, name='solution0'):
        self.instance = instance
        self.dict_sol = dict_sol
        self.df_flows = df_flows
        self.df_network = df_network
        self.df_flows['arc'] = list(zip(self.df_flows['origin'], self.df_flows['destination']))
        
    def solution_checker(self):
        c_transp = {**{arc:0 for arc in self.instance.arcs_e1}, **self.instance.cost_e2, **self.instance.cost_e2}
        self.df_flows['c_transport'] = self.df_flows['arc'].map(c_transp)
        self.df_flows['c_buy'] = self.df_flows['destination'].map(self.instance.c_buy)

        
        return True
        
