# Import other files
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict

# Import libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *

# Manual input data
file_path_data = directory("data") # folder containing data
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

print("Reserved FFR Capacity:", instance.Z_FFR.get_values()[None])
#print the average of R_FF_charge and R_FFR_discharge over time
import statistics as stat
print("Average R_FFR_charge:", stat.mean(instance.R_FFR_charge.get_values().values()))
print("Average R_FFR_discharge:", stat.mean(instance.R_FFR_discharge.get_values().values()))
from tools import print_exports
print_exports(instance, file_path_results, n_houses)

# Note 03/11 - Jakob
# Introduced the tools.py with simple functions for finding which constraints are binding and which are not. Those are called in the model_components_P2P.py. Also added simple printing for Z_FFR & R_FFR
# When setting p_FFR=0, I would assume the model to return the same results as the base case without FFR. This seems not to be the case.
# It seems like the constraint FFR_discharging_capacity is influencing the result in that case (at least commenting away the constraint gives the same result as the base case).'
# Need to look further into this. Could be a a problem with the model or a bug.