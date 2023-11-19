# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import file functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings, plot_state_of_charge, overview_plot, print_costs, costs_to_latex

#! Manual input data---------------------------------------------------------------------------------------------------------------------
file_path_data = directory('data') # Folder containing data
file_path_results = directory('results') # Folder containing the results

n_houses = 7
houses_bat = [97,50,26,68] # Indicate houses with batteries

houses_pv = [19,50,98,26,49,68] # Indicate houses with pv
capacity_pv = [5,5,5,5,5,5] # 5 kW of installed capacity for house 19,50,98,26,49,68

# Last day is not included in the model
start_date = '2021-4-01' # Between 2021-4-01 and 2021-6-30
end_date = '2021-7-01' # Between 2021-4-02 and 2021-7-01

FFR_type = 'No FFR' # 'Flex', 'Profil' or 'No FFR'

# System component switches (booleans)
P2P_switch = False
PV_switch = True
Battery_switch = False
Export_to_grid_switch = False

# Plot switches (booleans)
overview_plot_switch = True

print_Rs_switch = False
print_P2P_exports_switch = False
plot_state_of_charge_switch = False
cost_table_switch = False
costs_to_latex_switch = False

#!---------------------------------------------------------------------------------------------------------------------------------------

#$ Run the model for a continuous time period
continuous_switch = True
if continuous_switch:

    # Create dictionary of data with function generate_data_dict()
    data = generate_data_dict(file_path_data, start_date, end_date, houses_pv, houses_bat, capacity_pv, FFR_type, PV_switch, Battery_switch)

    # Run the model
    instance = model_p2p(data, P2P_switch, Export_to_grid_switch)

    # Printing functions
    if print_Rs_switch:
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

    if print_P2P_exports_switch:
        print_P2P_exports(instance, file_path_results, n_houses)

    if plot_state_of_charge_switch:
        plot_state_of_charge(instance, file_path_results, n_houses)

    if overview_plot_switch:
        overview_plot(instance)
    
    if cost_table_switch:
        print_costs(instance)
    
    if costs_to_latex_switch:
        costs_to_latex(instance)

    # Printing savings and soltuion cost
    solution_cost = instance.objective_function()

    savings = calculating_savings(instance, start_date, end_date)
    base_case = savings[0]
    P2P_savings = savings[1]
    FFR_savings = savings[2]
    Peak_savings = savings[3]
    G_export_savings = savings[4]

    unaccounted_savings = (base_case - solution_cost) - (P2P_savings + FFR_savings + Peak_savings + G_export_savings) #! Due to PV?
    
    # Print interesting values
    print(f'FFR type: {FFR_type}')
    print(f'The FFR price per [NOK/MW/hour]: {instance.p_FFR.value*1000}')
    print(f'Reserved FFR Capacity [kW]: {round(instance.Z_FFR.get_values()[None],2)}')

    print(f'\nNo P2P, batteries, PV production or export to grid (base case): {round(base_case,2)} NOK\n')

    print(f'P2P savings: {round(P2P_savings/base_case*100,2)}%')
    print(f'FFR savings: {round(FFR_savings/base_case*100,2)}%')
    print(f'Export to grid savings: {round(G_export_savings/base_case*100,2)}%')
    print(f'Peak savings (root cause = black box?): {round(Peak_savings/base_case*100,2)}%')
    print(f'Unaccounted savings (due to PV?): {round(unaccounted_savings/base_case*100,2)}%\n')

    print(f'The solution of the optimization gives a cost of: {round(solution_cost,2)} NOK')
    print(f'The total bill reduction is: {round((1-(solution_cost/base_case))*100,2)}%')