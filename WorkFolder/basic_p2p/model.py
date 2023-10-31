import numpy as np
import pandas as pd
from datetime import time
import matplotlib.pyplot as plt
from pyomo.environ import *
import pytz
import getpass


# Defining usernames to run code from two computers
current_user = getpass.getuser()
JK = "jakob"
OH = "olehermanimset"

def directory(folder):
    if current_user == JK:
        if folder == "data":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder/basic_p2p/data/test_case/"
        elif folder == "results":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder/basic_p2p//test_case/"
        else:
            print('Invalid directory input')
    elif current_user == OH:
        if folder == "data":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder/basic_p2p/data/'
        elif folder == "results":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder/basic_p2p/results/'
        else:
            print('Invalid directory input')
    else:
        print(f"Sorry, {current_user}, you are not the intended user.")

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

def generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv):
    list_houses = [f"H{i}" for i in range(1, n_houses + 1)]
    list_houses_pv = [f"H{i}" for i in houses_pv]
    list_houses_bat = [f"H{i}" for i in houses_bat]

    # transforming dates to align with data
    utc_tz = pytz.UTC  # just used to ensure matching the dates with the index
    start_date = pd.to_datetime(start_date_str, format='%Y-%m-%d').tz_localize(utc_tz)
    end_date = pd.to_datetime(end_date_str, format='%Y-%m-%d').tz_localize(utc_tz)

    # Get spot prices
    date_format_str = '%Y-%m-%d %H:%M:%S%z'  # '2019-12-06 14:00:00+00:00' format
    P_spot_df = pd.read_csv(file_path_data + r"dayahead_Jan_365days.csv", index_col=0,
                            parse_dates=[0], date_format=date_format_str)  # to make sure the date is read properly
    P_spot_df.index = P_spot_df.index.to_pydatetime() # convert to a datetime format required for the model
    P_spot_df = P_spot_df[["day ahead price (p/kWh)"]]  # get only price in pences/kWh
    P_spot_df_ = P_spot_df[(P_spot_df.index >= start_date) & (P_spot_df.index < end_date)]
    # Convert the dataframe P_spot_df_ to dictionary for data input for the function model_p2p()
    P_spot = P_spot_df_.to_dict()

    # Get demand
    P_demand_df = pd.read_csv(file_path_data + r"demand_Jan_365days.csv", index_col=0,
                              parse_dates=[0], date_format=date_format_str)  # to make sure the date is read properly
    P_demand_df.index = P_demand_df.index.to_pydatetime() # convert to a datetime format required for the model
    P_demand_df = P_demand_df[list_houses]  # Filter based on the houses selected
    P_demand_df.index = P_spot_df.index  # Change index from 2013 to 2019. The weeks of the days are the rest, so no more operations are needed
    P_demand_df_ = P_demand_df[(P_demand_df.index >= start_date) & (P_demand_df.index < end_date)]
    P_demand_df_ = P_demand_df_.stack()  # Set time and household as index
    # Convert the dataframe to dictionary
    P_demand = P_demand_df_.to_dict()

    # Get solar profiles, we assume the PV profile is the same for each house given that they are located close to each other
    PV_df = pd.read_csv(file_path_data + r"solar_profile_scenarios_yearly.csv", index_col=0,
                        parse_dates=[0], date_format=date_format_str)
    PV_df.index = PV_df.index.to_pydatetime() # convert to a datetime format required for the model
    scn = "1"
    PV_df = PV_df[[scn]]  # Select just one scenario, the data is prepared for several scenarios
    PV_df_ = PV_df[(PV_df.index >= start_date) & (PV_df.index < end_date)]
    # Convert the dataframe to dictionary
    PV = PV_df_.to_dict()

    # Set T
    list_T = P_spot_df_.index.to_list()

    # Parameter PV_cap
    PV_cap = {f"H{key}":capacity_pv[i] for i, key in enumerate(houses_pv)}

    # Scalars (single value parameters)
    Psi = 1 - 0.076  # Losses (assume a loss of 7.6% through the local network, Luth)
    Mu_c = 0.96  # Charging efficiency
    Mu_d = 0.96  # Discharging efficiency
    Alpha = 1.5  # charging rate 2.5 kW -> 1.25 kWh/hour at constant rate
    Beta = 1.5  # discharging rate 2.5 kW -> 1.25 kWh/hour at constant rate
    Smax = 4  # capacity batteries [kWh] # It can also be changes to be similar to parameter PV_cap where you specify the capacity of each battery
    Smin = Smax * 0.2  # minimum state of charge of batteries at all times
    S_init = Smax * 0.5  # initial state of charge of the battery
    #FFR related---------------------------------------------------------------------------------------------------------------------
    c_FFR = 0.0450 #[Pence/kWh]

    # Construct data dictionary
    data = {  # always start with None and then dictionary
        None: {  # names of the keys equal to the name of the parameteres in the model
            'H': {None: list_houses},  # providing data for set H
            'H_pv': {None: list_houses_pv},  # providing data for set H_pv
            "H_bat": {None: list_houses_bat},  # providing data for set H_bat
            "T": {None: list_T},  # providing datetime for set T
            # Parameters
            'P_spot': P_spot['day ahead price (p/kWh)'],
            "PV": PV[scn],
            "PV_cap": PV_cap,
            "Dem": P_demand,
            # Scalars
            "Psi": {None: Psi},
            "Mu_c": {None: Mu_c},
            "Mu_d": {None: Mu_d},
            "Alpha": {None: Alpha},
            "Beta": {None: Beta},
            "Smax": {None: Smax},
            "Smin": {None: Smin},
            "S_init": {None: S_init},
            "c_FFR": {None: c_FFR},
        }}

    return data

# Manual input data
file_path_data = directory('data') # folder containing data
file_path_results = directory('results') # folder containing the results

start_date_str = "2019-1-01"
end_date_str = "2019-1-02"

n_houses = 4
houses_pv = [1,2] # indicate houses with pv
capacity_pv = [5, 5] # 5 kW of installed capacity for house 1 and 2 respectively
houses_bat = [1,3] # indicate houses with batteries

# Create dictionary of data with function generate_data_dict()
data = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

# Checking data dictionary (if you want to check what has been constructed)
#data[None].keys() # Names of parameters
#data[None]["T"] # Substitute T if you want to check another parameter

# Run the model
instance = model_p2p(data)

# If you want to see the results, you can call the result as dictionary
x_p_dict = instance.x_p.get_values()
# Then you can convert it to dataframe
x_p_df = pd.DataFrame.from_dict(x_p_dict, orient="index")
x_p_df.columns = ["x_p"] # set a name for the dataframe
# In this case, you have a tuple as index, you need to separate them so that you can perform analysis
# First, set the index as a column
x_p_df = x_p_df.reset_index()
# Then, create one column for each element
x_p_df[['Time', 'Household', "Peer"]] = pd.DataFrame(x_p_df['index'].tolist(), index=x_p_df.index)
# Eliminate the index column containing the tuple
x_p_df = x_p_df.drop(columns='index')
# Set the columns as index again
x_p_df = x_p_df.set_index(["Time", "Household", "Peer"])

# Then you can plot the results or save it as excel
x_p_df.to_csv(file_path_results + "x_p.csv")

fig, ax = plt.subplots(figsize=(12,7))

x = x_p_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis

for house in x_p_df.index.get_level_values(1).unique():
    y = x_p_df[x_p_df.index.get_level_values(1) == house].values
    y_interval = np.empty(48)
    for time_step in range(int(len(y)/n_houses)):
        y_interval[time_step]=y[0+time_step*n_houses:3+time_step*n_houses].sum()
    ax.plot(x, y_interval, label=f"{house}")

ax.set_ylabel("Consumption from grid (kWh)")
ax.legend()

fig.tight_layout()
plt.show()