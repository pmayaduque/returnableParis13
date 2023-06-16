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

# 2.5 generation and demands
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

# 3.5 optimize the model
model.optimize()

# Print solution
if model.Status == GRB.OPTIMAL:
    # facility activation
    activ_f_sol = model.getAttr('X', activ_f)
    for c in collectors:
        for t in time:
            if activ_f_sol[c,t] > 0:
                print('activ_f(%s,  %s): %g' % (c, t, activ_f_sol[c,t]))
    activ_sol = model.getAttr('X', activ)
    for c in collectors:
        for t in time:
            if activ_sol[c,t] > 0:
                print('activ(%s,  %s): %g' % (c, t, activ_sol[c,t]))
    # flows from regions to collections
    print("Flow from regions to colllectors")
    flow_e1_sol = model.getAttr('X', flow_e1)
    for r,c,t in flow_e1:
        if flow_e1_sol[r,c,t]> 0:
            print('flow_e1(%s,  %s, %s): %g' % (r, c, t, flow_e1_sol[r,c,t])) 
    print("Flow collectors to transformers")
    flow_e2_sol = model.getAttr('X', flow_e2)
    for c,m,t in flow_e2:
        if flow_e2_sol[c,m,t]> 0:
            print('flow_e2(%s,  %s, %s): %g' % (c,m,t, flow_e2_sol[c,m,t])) 
    print("Flow transformers to producers")
    flow_e3_sol = model.getAttr('X', flow_e3)
    for m,p,t in flow_e3:
        if flow_e3_sol[m,p,t]> 0:
            print('flow_e3(%s,  %s, %s): %g' % (m,p,t, flow_e3_sol[m,p,t])) 
    print("Trips collectors  to transformers")
    trips_e2_sol = model.getAttr('X', trips_e2)
    for c,m,t in trips_e2:
        if trips_e2_sol[c,m,t]> 0:
            print('trips_e2(%s,  %s, %s): %g' % (c,m,t, trips_e2_sol[c,m,t]))
    print("Trips transformers to producers")
    trips_e3_sol = model.getAttr('X', flow_e3)
    for m,p,t in trips_e3:
        if flow_e3_sol[m,p,t]> 0:
            print('trips_e3(%s,  %s, %s): %g' % (m,p,t, trips_e3_sol[m,p,t])) 

            

# model.update()
# constraint = constr_relat2['c3',2]
# constraint_expr = model.getRow(constraint)
# # Print the mathematical expression of the constraint
# sense = constraint.getAttr(gp.GRB.Attr.Sense)
# rhs = constraint.getAttr(gp.GRB.Attr.RHS)

# expr_str = f"{constraint_expr} {sense} {rhs}"
# print(expr_str)