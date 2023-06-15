# 1. import the libraries
import gurobipy as gp
from gurobipy import GRB


# create a new model
m = gp.Model('returnability')

# 2. basic data
# 2.1. Sets
regions = ['r1', 'r2']
collect = ['c1', 'c2', 'c3']
manuf = ['m1', 'm2']
prod = ['p1', 'p2', 'p3']
time = ['t1', 't2', 't3', 't4']


# 2.2. Sparse network
# echelon 1 (regions to collections centers)
arcs_e1 = gp.tuplelist([('r1', 'c1'), 
                  ('r1', 'c2'),
                  ('r1', 'c3'),
                  ('r2', 'c1'), 
                  ('r2', 'c2'),
                  ('r2', 'c3')])

# echelon 2 (collection centers to manufacturers)
arcs_e2, cost_e2 = gp.multidict({
    ('c1', 'm1'):   100,
    ('c1', 'm2'):   90,
    ('c2', 'm1'):   80,
    ('c2', 'm2'):   15,
    ('c3', 'm1'):   35,
    ('c3', 'm2'):   28})

# echelon 3 (manufaturers to producers)
arcs_e3, cost_e3 = gp.multidict({
    ('m1', 'p1'):   100,
    ('m1', 'p2'):   90,
    ('m1', 'p3'):   80,
    ('m2', 'p1'):   100,
    ('m2', 'p2'):   90,
    ('m2', 'p3'):   80,
    ('m3', 'p1'):   100,
    ('m3', 'p2'):   90,
    ('m3', 'p3'):   80})

# 2.3 procesing costs
# 2.3.1. buying cost
c_buy = {'c1': 100,
         'c2': 90,
         'c3': 80
    }


# 3. modelling
# 3.1. create a new model
m = gp.Model('returnability')

# 3.2. create variables
flow_e1 = m.addVars(arcs_e1, time,  name="flow_e1")
flow_e2 = m.addVars(arcs_e2, time,  name="flow_e2")
flow_e3 = m.addVars(arcs_e3, time,  name="flow_e3")
activ = m.addVars(collect, time, vtype=gp.GRB.BINARY, name="activ")
activ_f = m.addVars(collect, time, vtype=gp.GRB.BINARY, name="activ_f")
stock = m.addVars(collect, time, name="stock")

# 3.3. create the objective function
obj = gp.LinExpr()
for r,c,t in flow_e1:
    obj += c_buy[c]*flow_e1[r,c,t]
#obj += 

