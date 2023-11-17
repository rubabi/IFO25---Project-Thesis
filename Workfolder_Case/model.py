# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import file functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings, plot_state_of_charge, overview_plot

#! Manual input data
file_path_data = directory("data") # folder containing data
file_path_results = directory('results') # folder containing the results

n_houses = 7
houses_pv = [2,3,4,5,6,7] # indicate houses with pv
capacity_pv = [3,5,5,5,5,5] # 3 kW and 5 kW of installed capacity for house 1 and 2,3,4,5,6,7 respectively
houses_bat = [1,3,5,7] # indicate houses with batteries

FFR_type = 'No FFR' # 'Flex', 'Profil' or 'No FFR'

#--------------------------------------------------------------------------------------------------------------------------------------

#$ Run the model for a continuous time period
continuous_switch = True
if continuous_switch:
    start_date = "2021-4-01"
    end_date = "2021-4-08" # Last day is not included in the model

    # Create dictionary of data with function generate_data_dict()
    data = generate_data_dict(file_path_data, start_date, end_date, houses_pv, houses_bat, capacity_pv, FFR_type)

    # Run the model
    instance = model_p2p(data)

    # Switches for what to print
    print_Rs = False
    print_P2P_exports_switch = True
    plot_state_of_charge_switch = False
    overview_plot_switch = False

    # Printing functions
    if print_Rs:
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
        overview_plot(instance, file_path_results, n_houses)

    # Printing savings
    savings = calculating_savings(instance, start_date, end_date)
    no_savings = savings[0]
    bill_reduction = savings[1]
    P2P_savings = savings[2]
    FFR_savings = savings[3]
    
    # Print interesting values
    print(f'FFR type: {FFR_type}')
    print(f'The FFR price per [NOK/mW/hour]: {instance.p_FFR.value*1000}')
    print(f'Reserved FFR Capacity [kW]: {round(instance.Z_FFR.get_values()[None],2)}')
    print(f'\nNo P2P, batteries or PV production (base case): {round(no_savings,2)} NOK\n')
    print(f'P2P savings: {round(P2P_savings/no_savings*100,2)}%')
    print(f'FFR savings: {round(FFR_savings/no_savings*100,2)}%\n')
    print(f'The total bill reduction is: {round(float(bill_reduction)*100,2)}%')

#--------------------------------------------------------------------------------------------------------------------------------------

#$ Run the model for multiple, discrete weeks
discrete_switch = False
if discrete_switch:
    week_list = [["2021-4-01","2021-4-08"],["2021-5-01","2021-5-08"],["2021-6-01","2021-6-08"],["2021-7-01","2021-7-08"],["2021-8-01","2021-8-08"]] # Last day is not included in the model
    no_savings_discrete = 0
    bill_reduction_discrete = 0
    P2P_savings_discrete = 0
    FFR_savings_discrete = 0
    reserved_FFR_capacity = []

    for week in week_list:
        start_date = week[0]
        end_date = week[1]
        data_week = generate_data_dict(file_path_data, start_date, end_date, houses_pv, houses_bat, capacity_pv, FFR_type)

        # Run an instance of the model for a week
        instance = model_p2p(data_week)
        savings = calculating_savings(instance, start_date, end_date)
        no_savings_discrete += savings[0]
        bill_reduction_discrete += savings[1]/len(week_list)
        P2P_savings_discrete += savings[2]
        FFR_savings_discrete += savings[3]
        reserved_FFR_capacity.append(round(instance.Z_FFR.get_values()[None],2))

    print(f'The FFR price per [NOK/mW]: {instance.p_FFR.value*1000}')
    print(f'Reserved FFR Capacity [kW]: {reserved_FFR_capacity}')
    print(f'\nNo P2P, batteries or PV production (base case): {round(no_savings_discrete,2)} NOK\n')
    print(f'P2P savings: {round(P2P_savings_discrete/no_savings_discrete*100,2)}%')
    print(f'FFR savings: {round(FFR_savings_discrete/no_savings_discrete*100,2)}%')
    print(f'The total bill reduction is: {round(bill_reduction_discrete*100,2)}%\n')