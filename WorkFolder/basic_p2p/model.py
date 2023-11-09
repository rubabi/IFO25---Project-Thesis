# Import files 
import model_components_P2P
import directories_P2P
import generate_data
import tools

# Import flie functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings

# Import libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
import statistics as stat

# Manual input data
file_path_data = directory("data") # folder containing data
file_path_results = directory('results') # folder containing the results

start_date_str = "2019-1-01"
end_date_str = "2019-1-2"

n_houses = 4
houses_pv = [1,2] # indicate houses with pv
capacity_pv = [5,5] # 5 kW of installed capacity for house 1 and 2 respectively
houses_bat = [1,3] # indicate houses with batteries

# Create dictionary of data with function generate_data_dict()
data = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

# Checking data dictionary (if you want to check what has been constructed)
#data[None].keys() # Names of parameters
#data[None]["T"] # Substitute T if you want to check another parameter

# Run the model
instance = model_p2p(data)

# Print interesting values
print(f'The FFR price set: {instance.p_FFR.value}')
print(f'Reserved FFR Capacity: {round(instance.Z_FFR.get_values()[None],2)}')

# Printing the R_FFR_charge/discharge values
print_Rs = 0
if print_Rs == 1:
    from collections import defaultdict

    total_reserved_per_timestamp = defaultdict(float)

    for (timestamp, house), reserved in instance.R_FFR_charge.get_values().items():
        total_reserved_per_timestamp[timestamp] += reserved

    for timestamp, total_reserved in total_reserved_per_timestamp.items():
        print(f'Timestamp: {timestamp}, Total Reserved in R: {round(total_reserved,2)}')

    total_discharged_per_timestamp = defaultdict(float)

    for (timestamp, house), discharged in instance.R_FFR_discharge.get_values().items():
        total_discharged_per_timestamp[timestamp] += discharged

    for timestamp, total_discharged in total_discharged_per_timestamp.items():
        print(f'Timestamp: {timestamp}, Total Discharged in R: {round(total_discharged,2)}')

# Printing P2P exports
#print_P2P_exports(instance, file_path_results, n_houses)

# Printing savings
savings = calculating_savings(instance,n_houses, start_date_str, end_date_str)
no_savings = savings[0]
bill_reduction = savings[1]
P2P_savings = savings[2]
FFR_savings = savings[3]

print(f'The total bill reduction is: {round(bill_reduction*100,2)}%')
print(f'No savings: {round(no_savings,2)} pence')
print(f'P2P savings: {round(P2P_savings/no_savings*100,2)}%')
print(f'FFR savings: {round(FFR_savings/no_savings*100,2)}%')