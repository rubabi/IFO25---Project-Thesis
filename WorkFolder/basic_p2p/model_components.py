import pandas as pd
from datetime import time
from pyomo.environ import *

def model_p2p(data):
    model = AbstractModel()

    # Sets
    model.T = Set() # Time period (e.g., hour, half-an-hour)
    model.H = Set() # Households
    model.H_pv = Set() # Set of Households with PV
    model.H_bat = Set() # Set of Households with Batteries
    model.P = model.H*model.H # Subset of network in the community (dim=2, H, H) (eg. P={(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)})

    # Parameters
    model.P_spot = Param(model.T) # Spot price for electricity
    model.PV = Param(model.T) # PV production at each time and household with PV panels
    model.Dem = Param(model.T, model.H) # Demand at each time and household

    model.PV_cap = Param(model.H_pv) # Installed capacity PV for each house with pv

    model.Psi = Param(initialize=1 - 0.076,
                      doc="% of losses")  # Losses in the community lines The local trade assumes losses of 7.6% through the local network (see [40]) in luth.

    model.Mu_c = Param()  # charging efficiency
    model.Mu_d = Param() # discharge efficiency
    model.Alpha = Param()  # charging rate 2.5 kW -> 2.5 kWh/hour at constant rate
    model.Beta = Param()  # discharging rate 2.5 kW -> 2.5 kWh/hour at constant rate, etha in Stai
    model.Smax = Param()  # capacity batteries [kWh]
    model.Smin = Param()  # [kWh] here 20% of the maximum capacity
    model.S_init = Param()  # [kWh] initial battery state
    model.c_FFR = Param()

    # Variables
    model.x_g = Var(model.T, model.H, within=NonNegativeReals)  # sold power to community c, G in Luth
    model.d = Var(model.T, model.H_bat, within=NonNegativeReals)  # discharge from batteries
    model.c = Var(model.T, model.H_bat, within=NonNegativeReals)  # charging from batteries
    model.s = Var(model.T, model.H_bat, within=NonNegativeReals)  # state of battery, w^{charge} in FFR-paper

    #FFR related Variables----------------------------------------------------------------------------------------------------------------------
    model.z_FFR = Var(within=NonNegativeReals) #FFR capacity
    model.r_FFR_charge = Var(model.T, model.H_bat, within=NonNegativeReals) #FFR capacity from charging house h in time step t [kwh]
    model.r_FFR_discharge = Var(model.T, model.H_bat, within=NonNegativeReals) #FFR capacity from discharging h in time step t [kwh]
    #---------------------------------------------------------------------------------------------------------------------------------------------


    model.x = Var(model.T, model.H, within=NonNegativeReals)  # total exports house h
    model.x_p = Var(model.T, model.P, within=NonNegativeReals)  # exports from house h to house p
    model.i = Var(model.T, model.H, within=NonNegativeReals)  # total imports house h
    model.i_p = Var(model.T, model.P, within=NonNegativeReals)  # imports of house h from house p

    # Objective function - Added FFR
    def objective_function(model):
        return sum(model.P_spot[t] * model.x_g[t, h] for t in model.T for h in model.H) - model.c_FFR*model.z_FFR
    model.objective_function = Objective(rule=objective_function, sense=minimize)

    def balance_equation(model, t, h): # For each time and household, (1) in Luth
        return (model.x_g[t, h] + (model.PV[t] if h in model.H_pv else 0)  + (model.d[t,h] if h in model.H_bat else 0)
                + model.i[t, h] >= model.Dem[t, h] + model.x[t, h] + (model.c[t, h] if h in model.H_bat else 0))
    model.balance_equation = Constraint(model.T, model.H, rule=balance_equation)

    #FFR Constraints---------------------------------------------------------------------------------------------------------------------------------------------
    def FFR_charging_capacity(model, t, h):
        return model.c[t,h] >= model.r_FFR_charge[t,h]    
    model.FFR_charging_capacity = Constraint(model.T, model.H_bat, rule=FFR_charging_capacity)

    def FFR_discharging_capacity(model,t,h):
        return model.d[t, h] + model.r_FFR_discharge[t, h] >= model.Beta    
    model.FFR_discharging_capacity = Constraint(model.T, model.H_bat, rule=FFR_discharging_capacity)

    def FFR_capacity_sum(model,t, h):
        return sum(model.r_FFR_charge[t,h] + model.r_FFR_discharge[t, h] for h in model.H_bat) >= model.z_FFR    
    model.FFR_capacity_sum = Constraint(model.T, model.H_bat, rule=FFR_capacity_sum)
    #---------------------------------------------------------------------------------------------------------------------------------------------------------------

    # P2P constraints
    def sum_exports_household(model, h, t): # (2)
        return model.x[t, h] == sum(model.x_p[t, p] for p in model.P if p[0] == h)
    model.sum_exports_household = Constraint(model.H, model.T, rule=sum_exports_household)

    def sum_imports_household(model, h, t): # (4)
        return model.i[t, h] == sum(model.i_p[t, p] for p in model.P if p[0] == h)
    model.sum_imports_household = Constraint(model.H, model.T, rule=sum_imports_household)

    def balance_exports_imports(model, t): # (5)
        return sum(model.i[t, h] for h in model.H) == model.Psi * sum(model.x[t, h] for h in model.H)
    model.balance_exports_imports = Constraint(model.T, rule=balance_exports_imports)

    def balance_exports_imports_household(model, t, h0, h1): #(3)
        return model.i_p[t, h0, h1] == model.Psi * model.x_p[t, h1, h0]
    model.balance_exports_imports_household = Constraint(model.T, model.P, rule=balance_exports_imports_household)

    # Battery constraints

    def time_constraint(model, t, h):
        if t.time() == time(0,0): # when the hour is 00:00
            return model.s[t, h] == model.S_init + model.Mu_c * model.c[t, h] - 1/model.Mu_d * model.d[t, h]
        else:
            t_previous = t - pd.Timedelta(minutes=30)  # Calculate your previous t, change depending on your delta time
            return model.s[t, h] == model.s[t_previous, h] + model.Mu_c * model.c[t, h] - 1/model.Mu_d * model.d[t, h]
    model.time_constraint = Constraint(model.T, model.H_bat, rule=time_constraint)

    def min_SoC(model, t, h): #(7)
        return model.s[t, h] >= model.Smin
    model.min_SoC = Constraint(model.T, model.H_bat, rule=min_SoC)

    def charging_rate(model, t, h): #(8)
        return model.c[t, h] <= model.Alpha
    model.charging_rate = Constraint(model.T, model.H_bat, rule=charging_rate)

    def discharge_rate(model, t, h): #(8)
        return model.d[t, h] <= model.Beta
    model.discharge_rate = Constraint(model.T, model.H_bat, rule=discharge_rate)

    def max_SoC(model, t, h): #(7)
        return model.s[t, h] <= model.Smax
    model.max_SoC = Constraint(model.T, model.H_bat, rule=max_SoC)

    instance = model.create_instance(data)
    results = SolverFactory("glpk", Verbose=True).solve(instance, tee=True)
    results.write()
    instance.solutions.load_from(results)

    return instance