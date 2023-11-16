# Import file functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings, plot_state_of_charge, overview_plot

# Manual input data
file_path_data = directory("Test case") # folder containing data
file_path_results = directory('results') # folder containing the results

n_houses = 7
houses_pv = [2,3,4,5,6,7] # indicate houses with pv
capacity_pv = [3,5,5,5,5,5] # 3 kW and 5 kW of installed capacity for house 2 and 2,3,4,5,6,7 respectively
houses_bat = [1,3,5,7] # indicate houses with batteries
#--------------------------------------------------------------------------------------------------------------------------------------

# Run the model for a continuous time period
continuous_switch = True
if continuous_switch:
    start_date_str = "2021-4-01"
    end_date_str = "2021-4-30"

    # Create dictionary of data with function generate_data_dict()
    data = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

    # Run the model
    instance = model_p2p(data)

    # Print interesting values
    print(f'The FFR price per [NOK/kW]: {instance.p_FFR.value*2}')
    print(f'Reserved FFR Capacity [kW]: {round(instance.Z_FFR.get_values()[None],2)}')

    # Switches for what to print
    print_Rs = False
    print_P2P_exports_switch = False
    plot_state_of_charge_switch = False
    overview_plot_switch = True

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
    savings = calculating_savings(instance, n_houses, start_date_str, end_date_str)
    no_savings = savings[0]
    bill_reduction = savings[1]
    P2P_savings = savings[2]
    FFR_savings = savings[3]

    print(f'The total bill reduction is: {round(bill_reduction*100,2)}%')
    print(f'No P2P, batteries or PV production (base case): {round(no_savings,2)} pence')
    print(f'P2P savings: {round(P2P_savings/no_savings*100,2)}%')
    print(f'FFR savings: {round(FFR_savings/no_savings*100,2)}%')
#--------------------------------------------------------------------------------------------------------------------------------------

# Run the model for multiple, discrete weeks
discrete_switch = False
if discrete_switch:
    week_list = [["2019-1-01","2019-1-08"],["2019-4-01","2019-4-08"],["2019-7-01","2019-7-08"],["2019-10-01","2019-10-08"]]
    no_savings_discrete = 0
    bill_reduction_discrete = 0
    P2P_savings_discrete = 0
    FFR_savings_discrete = 0
    reserved_FFR_capacity = []

    for week in week_list:
        start_date_str = week[0]
        end_date_str = week[1]
        data_week = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

        # Run an instance of the model for a week
        instance = model_p2p(data_week)
        savings = calculating_savings(instance, n_houses, start_date_str, end_date_str)
        no_savings_discrete += savings[0]
        bill_reduction_discrete += savings[1]/len(week_list)
        P2P_savings_discrete += savings[2]
        FFR_savings_discrete += savings[3]
        reserved_FFR_capacity.append(round(instance.Z_FFR.get_values()[None],2))

    print(f'The FFR price per [pence/kW]: {instance.p_FFR.value*2}')
    print(f'Reserved FFR Capacity [kW]: {reserved_FFR_capacity}')
    print(f'No P2P, batteries or PV production (base case): {round(no_savings_discrete,2)} pence')
    print(f'P2P savings: {round(P2P_savings_discrete/no_savings_discrete*100,2)}%')
    print(f'FFR savings: {round(FFR_savings_discrete/no_savings_discrete*100,2)}%')
    print(f'The total bill reduction is: {round(bill_reduction_discrete*100,2)}%')