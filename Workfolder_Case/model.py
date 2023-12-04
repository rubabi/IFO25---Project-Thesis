# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import file functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings, plot_state_of_charge, overview_plot, print_costs, costs_to_latex

#! Manual input data --------------------------------------------------------------------------------------------------------------------
#$ File paths
file_path_data = directory('data') # Folder containing data
file_path_results = directory('results') # Folder containing the results

#$ Input data
n_houses = 7
houses_bat = [97,50,26,68] # Indicate houses with batteries
houses_pv = [19,50,98,26,49,68] # Indicate houses with pv
capacity_pv = [5,5,5,5,5,5] # 5 kW of installed capacity for house 19,50,98,26,49,68

#$ Time period
start_date = '2021-4-01' # Between 2021-4-01 and 2021-6-30
end_date = '2021-7-01' # Between 2021-4-02 and 2021-7-01, end date is not included in the time period

#$ 'Flex', 'Profil' or 'No FFR'
FFR_type = 'Flex'
if FFR_type != 'No FFR' and FFR_type != 'Flex' and FFR_type != 'Profil':
    raise ValueError('FFR_type must be either "Flex", "Profil" or "No FFR"') 

    raise ValueError('reference_case must be either "No FFR" or "Naked case"')

#$ System component switches (booleans)
P2P_switch = True
PV_switch = True
Battery_switch = False
Export_to_grid_switch = True

#$ Plot switches (booleans)
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
    naked_case = savings[0]
    P2P_savings = savings[1]
    FFR_savings = savings[2]
    Peak_savings = savings[3]
    G_export_savings = savings[4]

    unaccounted_savings = (naked_case - solution_cost) - (P2P_savings + FFR_savings + Peak_savings + G_export_savings) #! Due to PV?
    
    # Print interesting values
    print(f'From {start_date} to {end_date}\n')
    print(f'FFR type: {FFR_type}')
    print(f'The FFR price per [NOK/MW/hour]: {instance.p_FFR.value*1000}')
    print(f'Reserved FFR Capacity [kW]: {round(instance.Z_FFR.get_values()[None],2)}')

    print(f'\nNaked Case: {round(naked_case,2)} NOK')
    print(f'The solution of the optimization gives a cost of: {round(solution_cost,2)} NOK')
    print(f'Total savings: {round(naked_case-solution_cost,2)} NOK')

    '''print(f'\nSavings breakdown')
    print(f'P2P savings: {round(P2P_savings,2)} NOK')
    print(f'FFR savings: {round(FFR_savings,2)} NOK')
    print(f'Export to grid savings: {round(G_export_savings,2)} NOK')
    print(f'Peak savings: {round(Peak_savings,2)} NOK')
    print(f'Unaccounted savings (due to PV?): {round(unaccounted_savings,2)} NOK\n')'''