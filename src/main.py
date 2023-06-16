# 1. import the libraries
import gurobipy as gp
from gurobipy import GRB


# create a new model
m = gp.Model('returnability')

# 2. basic data
# 2.1. Sets
regions = ['r1', 'r2']
collectors = ['c1', 'c2', 'c3']
manufs = ['m1', 'm2']
producers = ['p1', 'p2', 'p3']
time = [1, 2, 3, 4]


# 2.2. Sparse network
# echelon 1 (regions to collections centers)
arcs_e1 = gp.tuplelist([('r1', 'c1'), 
                        ('r1', 'c2'),
                        ('r1', 'c3'),
                        ('r2', 'c1'), 
                        ('r2', 'c2'),
                        ('r2', 'c3')])
#arcs_e1 = [(a[0], a[1], t) for a in arcs_e1 for t in time]

# echelon 2 (collection centers to manufacturers)
arcs_e2, cost_e2 = gp.multidict({
    ('c1', 'm1'):   100,
    ('c1', 'm2'):   90,
    ('c2', 'm1'):   80,
    ('c2', 'm2'):   15,
    ('c3', 'm1'):   35,
    ('c3', 'm2'):   28})
#arcs_e2 = [(a[0], a[1], t) for a in arcs_e2 for t in time]

# echelon 3 (manufaturers to producers)
arcs_e3, cost_e3 = gp.multidict({
    ('m1', 'p1'):   100,
    ('m1', 'p2'):   90,
    ('m1', 'p3'):   80,
    ('m2', 'p1'):   100,
    ('m2', 'p2'):   90,
    ('m2', 'p3'):   80})
#arcs_e3 = [(a[0], a[1], t) for a in arcs_e3 for t in time]

# 2.3 procesing costs
# buying cost
c_buy = {'c1': 100,
         'c2': 90,
         'c3': 80
    }
# classifying cost
c_clasif ={'c1': 10,
           'c2': 9,
           'c3': 8
    }
# collection center activation cost
c_activ ={'c1': 100,
          'c2': 100,
          'c3': 100
    }
# collection center activation cost
c_hold ={'c1': 1,
         'c2': 1,
         'c3': 1
    }
#  cleaning cost
c_clean={'m1': 10,
         'm2': 9
    }

# 2.4 Capacities
# vehicle capacity
capV = 100 
# generation in each region
gen = {'r1': 500,
        'r2': 300
    }
# classification capacity
capC = {'c1': 300,
        'c2': 250,
        'c3': 300
    }
# sortage capacity
capS = {'c1': 900,
        'c2': 750,
        'c3': 600
    }
# initial stock at collection center
iniS = {'c1': 1,
        'c2': 1,
        'c3': 1
    }
# transformer capacity
capM = {'m1': 900,
        'm2': 750
    }

# 2.5 demands
demP = {'p1': 300,
        'p2': 250,
        'p3':100}
# commercial relationship min duration
dt = 2


# 3. modelling
# 3.1. create a new model
model = gp.Model('returnability')

# 3.2. create variables
flow_e1 = model.addVars(arcs_e1, time,  name="flow_e1")
flow_e2 = model.addVars(arcs_e2, time,  name="flow_e2")
flow_e3 = model.addVars(arcs_e3, time,  name="flow_e3")
activ = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ")
activ_f = model.addVars(collectors, time, vtype=gp.GRB.BINARY, name="activ_f")
stock = model.addVars(collectors, time, name="stock")

# 3.3. create the objective function
obj = gp.LinExpr()
# 3.3.1. buying and classification cost
for r,c,t in flow_e1:
    obj += c_buy[c]*flow_e1[r,c,t] + c_clasif[c]*flow_e1[r,c,t]
    
# 3.3.2. transforming (cleaning)
for m,p,t in flow_e3:
    obj += c_clean[m]*flow_e3[m,p,t] 

# 3.3.3. collection center activation cost and inventory holding
for c,t in [(c,t) for c in collectors for t in time]:
    obj += c_activ[c]*activ[c,t] + c_hold[c]*stock[c,t]

# 3.3.4 transport from collections to transformers
for c,m,t in flow_e2:
    obj += cost_e2[c,m]*flow_e2[c,m,t] / capV

# 3.3.4 transport from transformers to producers 
for c,m,t in flow_e2:
    obj += cost_e2[c,m]*flow_e2[c,m,t] / capV
    
# set the objective 
model.setObjective(obj, GRB.MINIMIZE)

# 3.4. Constraints

# classification capacity
constr_capC = model.addConstrs(
    (flow_e1.sum('*', c, t) <= capC[c] for c, t in [(c, t) for c in collectors for t in time]), "capC")

# generation at each region
constr_gen = model.addConstrs(
    (flow_e1.sum(r, '*', t) <= gen[r] for r, t in [(r, t) for c in regions for t in time]), "gen")

# storage capacity
constr_capS = model.addConstrs(
    (stock[c,t]<=capS[c] for c, t in [(c, t) for c in collectors for t in time]), "capS")

# transformer capacity
constr_capM = model.addConstrs(
    (flow_e2.sum('*', m, t) <= capM[m] for m, t in [(m, t) for m in manufs for t in time]), "capM")

# stock balance
def prev_stock(c,t):
    if t <= 1:
        return iniS[c]
    return stock[c,t]
    
cosntr_stock = model.addConstrs(
    (stock[c,t] == prev_stock(c,t) + flow_e1.sum('*', c, t) - flow_e2.sum(c,'*', t) for c, t in [(c, t) for c in collectors for t in time]), "stock")


# demand fulfillment
constr_demP = model.addConstrs(
    (flow_e3.sum('*',p, t) <= demP[p] for p, t in [(p, t) for p in producers for t in time]), "demP")

# commercial relationship
constr_relat1 = model.addConstrs(
    (activ[c,t] >= activ_f[c,t1] for c, t1, t in [(c, t1, t) for c in collectors for t1 in time for t in range(t1, min(t1+dt, len(time)))]))
def prev_actv(c, t):
    if t <=1:
        return 0
    return activ[c,t-1]
    
constr_relat2 = model.addConstrs(
    activ_f[c,t]>=activ[c,t] - prev_actv(c, t) for c in collectors for t in time
    )

model.update()
constraint = constr_relat2['c3',2]
constraint_expr = model.getRow(constraint)
# Print the mathematical expression of the constraint
sense = constraint.getAttr(gp.GRB.Attr.Sense)
rhs = constraint.getAttr(gp.GRB.Attr.RHS)

expr_str = f"{constraint_expr} {sense} {rhs}"
print(expr_str)