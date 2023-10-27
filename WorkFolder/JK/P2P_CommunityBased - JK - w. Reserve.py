"""
Created on Sun Mar  7 17:41:17 2021

@author: seyednh
"""

from pyomo.environ import *
import pandas as pd
import numpy as np
from pyomo.opt import SolverFactory
import pyomo as pyo

#Add FFR market price from Stai&Backe
c_FFR = 450 #[NOK/MW/h]

# address = 'C:\Users\Mousa\PycharmProjects\Pyomo\InputData.xlsx'


BatteryPlace=np.array([1, 1, 0, 1]); #Defines if a house has a battery or not I think

#Function for reading data from excel files.
# Dem = Demand from house h in time step t
# Wind = Wind production of house h in time step t
# PV = Photovoltaic productuin of house h in time step t
# Pg = Price of electricity from the grid in time step t
# RES = Renewable energy production of house h in time step t
# Nh = Number of houses
# Nt = Number of time steps
# BatteryInput = scalars for battery(???)

def InputParam(address):
    DemDF = pd.read_excel(address, sheet_name='Demand_houses')
    Dem = DemDF.to_numpy()

    WindDF = pd.read_excel(address, sheet_name='Wind_input')
    Wind = WindDF.to_numpy()

    PVDF = pd.read_excel(address, sheet_name='PV_input')
    PV = PVDF.to_numpy()

    PgDF = pd.read_excel(address, sheet_name='Elec_price')
    Pg = PgDF.to_numpy()
    Pg = dict(enumerate(Pg.flatten(), 0))
    print(type(Pg))

    RES = PV + Wind
    Nh = len(Dem[0, :])
    Nt = len(Dem[:, 0])
    
    Battery_DF = pd.read_excel(address, sheet_name='Battery_input')
    BatteryInput = Battery_DF.to_numpy()
    
    
    
    return Dem, Pg, RES, Nh, Nt, BatteryInput


Dem, Pg, res, Nh, Nt, BatteryInput = InputParam("C:/Users/jakob/Downloads/InputData p.xlsx")


#Dem, Pg, res, Nh, Nt, BatteryInput = InputParam('C:/Naser/Python Book/P2PMarket/InputData25Houses.xlsx')


Battery_Ub=BatteryInput[0]; # s: Battery upper bound
Battery_Lb=BatteryInput[1]; # s: Battery lower bound
Battery_ChargeRate=BatteryInput[2]; # alpha: Maximum battery charge rate
Battery_disChargeRate=BatteryInput[3]; # beta: Maximum battery discharge rate
Battery_ChargeEff=BatteryInput[4]; # etha_c: Battery charging efficiency
Battery_disChargeEffb=BatteryInput[5]; # etha_d: Battery discharging efficiency

#%%

model = ConcreteModel()

# Define model Parameters
model.Nh = RangeSet(0, Nh-1, 1) #Houses
model.Np = RangeSet(0, Nh - 2, 1) #Peers = Houses-1
model.Nt = RangeSet(0, Nt-1, 1) #Time steps


# declare decision variables
model.G = Var(model.Nt, model.Nh, domain=NonNegativeReals) #Grid consumption of house h in time step t
model.X_p = Var(model.Nt, model.Nh, model.Np, domain=NonNegativeReals) #P2P electricity sale of house h to peer p in time step 
model.I_p = Var(model.Nt, model.Nh, model.Np, domain=NonNegativeReals) #P2P electricity purchase of house h from peer p in time step t
#Add FFR capacity
model.z_FFR = Var(domain=NonNegativeReals)


if sum(BatteryPlace)>0:
   model.Bat = RangeSet(0, sum(BatteryPlace)-1, 1) # Defining a range of integers from 0 to batteryplace-1

   model.C = Var(model.Nt, model.Bat, domain=NonNegativeReals, bounds=(0,Battery_ChargeRate)) #Charge of batteries in the range model.Bat in each time step t. Including non-negative constraint and charging rate, eq. 8 in Luth
   model.D = Var(model.Nt, model.Bat, domain=NonNegativeReals, bounds=(0,Battery_disChargeRate)) #Discharge of batteries in the range model.Bat in each time step t. Including non-negative constraint and dischargingcharging rate, eq. 9 in Luth
   model.S = Var(model.Nt, model.Bat, domain=NonNegativeReals, bounds=(Battery_Lb,Battery_Ub)) #Energy storage of batteries in the range model.Bat in each time step t. Including non-negative constraints and upper/lower bounds of battery, eq. 7 in Luth



#%%
# declare objective
def obj_rule(model):
    return sum(Pg[t] * model.G[t, h] for h in model.Nh for t in model.Nt) #Eq. 6 in Luth, objective

model.obj = Objective(rule=obj_rule, sense=minimize) 
#%%
PsiP2P = 1 - 0.076 #Distribution network losses and conversion of DG for P2P sale

IXpind = np.zeros([Nh - 1, Nh],dtype=int) #P2P electricity trading matrix from house to peer. Every column (i) corresponds to a house, every row(j) corresponds to a peer. 
for i in range(Nh):
    for j in range(Nh - 1):
        if i <= j:
            IXpind[j, i] = j + 1
        else:
            IXpind[j, i] = j 

model.P2P = ConstraintList() #Initializing constraintlist 
k=-1
for i in model.Nh:
    if BatteryPlace[i]!=0: #House has battery
      k=k+1
      
      model.P2P.add(model.S[0,k]==0+Battery_ChargeEff*model.C[0,k] - (1/Battery_disChargeEffb)*model.D[0,k]) #Storage level of battery. Equation 10 in Luth when t = 0
      #model.P2P.add(model.S[Nt-1,k]==1)
      for t in range(1,Nt):
          model.P2P.add(model.S[t,k]==model.S[t-1,k] + Battery_ChargeEff*model.C[t,k] - (1/Battery_disChargeEffb)*model.D[t,k]) #Storage level of battery in each time step. Eq. 10 in Luth when t != 0
          
      
      
      for t in model.Nt:
         model.P2P.add(res[t,i]+model.G[t,i] + model.D[t,k] +sum(model.I_p[t,i,j] for j in model.Np)>=Dem[t,i]+ model.C[t,k]+sum(model.X_p[t,i,j] for j in model.Np)) #Balance in Supply and demand. Eq. 1 in Luth
         for j in model.Np:
             b=np.asarray(np.where(IXpind[:,IXpind[j,i]] == i))
             model.P2P.add(model.I_p[t, i, j] == PsiP2P * model.X_p[t, IXpind[j, i] ,b[0,0]]) #Eq. 3 in Luth
             
    elif BatteryPlace[i]==0: #House has no battery
        for t in model.Nt:
           model.P2P.add(res[t,i]+model.G[t,i]+sum(model.I_p[t,i,j] for j in model.Np)>=Dem[t,i]+sum(model.X_p[t,i,j] for j in model.Np)) #Balance in supply and demand w.o. battery. Eq. 1 in Luth
           for j in model.Np:
               b=np.asarray(np.where(IXpind[:,IXpind[j,i]] == i))
               model.P2P.add(model.I_p[t, i, j] == PsiP2P * model.X_p[t, IXpind[j, i] ,b[0,0]]) #Eq. 3 in Luth
        

#%%         
'''
def con_rule(model, Nh):
   PsiP2P = 1 - 0.076
   IXpind = np.zeros([Nh - 1, Nh],dtype=int)
   for i in range(Nh):
       for j in range(Nh - 1):
           if i <= j:
               IXpind[j, i] = j + 1
           else:
               IXpind[j, i] = j 
   
   model.P2P = ConstraintList()
   for i in model.Nh:
       if BatteryPlace[i]!=0:
         for t in model.Nt:
            model.P2P.add(res[t,i]+model.G[t,i]+sum(model.I_p[t,i,j] for j in model.Np)>=Dem[t,i]+sum(model.X_p[t,i,j] for j in model.Np))
            for j in model.Np:
                b=np.asarray(np.where(IXpind[:,IXpind[j,i]] == i))
                model.P2P.add(model.I_p[t, i, j] == PsiP2P * model.X_p[t, IXpind[j, i] ,b[0,0]])
'''    




#%%
#results = SolverFactory("GLPK", Verbose=True).solve(model,tee=True)

model.pprint()

#%%
#opt = SolverFactory('glpk')
#opt.solve(model)

#%%
opt = SolverFactory('glpk')
opt.solve(model) 



#%%
for key in model.G:
    print(value(model.G[key]))
    
value(model.obj)
print(value(model.obj))


#%%
'''
for key in model.C:
    print(value(model.C[key]))

for key in model.D:
    print(value(model.D[key]))
    
for key in model.I_p:
    print(value(model.I_p[key]))

for key in model.X_p:
    print(value(model.X_p[key]))
#%%
'''
