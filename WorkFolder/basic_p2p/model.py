# Import flie functons
from model_components_P2P import model_p2p
from directories_P2P import directory
from generate_data import generate_data_dict
from tools import print_P2P_exports, calculating_savings, plot_state_of_charge, overview_plot

# Manual input data
file_path_data = directory("data") # folder containing data
file_path_results = directory('results') # folder containing the results

start_date_str = "2019-1-01"
end_date_str = "2019-1-08"

n_houses = 4
houses_pv = [1,2] # indicate houses with pv
capacity_pv = [5,5] # 5 kW of installed capacity for house 1 and 2 respectively
houses_bat = [1,3] # indicate houses with batteries

# Create dictionary of data with function generate_data_dict()
data = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

# Run the model
instance = model_p2p(data)

# Print interesting values
print(f'The FFR price per [pence/kW]: {instance.p_FFR.value*2}')
print(f'Reserved FFR Capacity [kW]: {round(instance.Z_FFR.get_values()[None],2)}')

# Switches for what to print
print_Rs = False
print_P2P_exports_switch = False
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
savings = calculating_savings(instance,n_houses, start_date_str, end_date_str)
no_savings = savings[0]
bill_reduction = savings[1]
P2P_savings = savings[2]
FFR_savings = savings[3]

print(f'The total bill reduction is: {round(bill_reduction*100,2)}%')
print(f'No P2P, batteries or PV production (base case): {round(no_savings,2)} pence')
print(f'P2P savings: {round(P2P_savings/no_savings*100,2)}%')
print(f'FFR savings: {round(FFR_savings/no_savings*100,2)}%')

week_list = [["2019-1-01","2019-1-08"],["2019-4-01","2019-4-08"],["2019-7-01","2019-7-08"],["2019-10-01","2019-10-08"]]
for week in week_list:
    start_date_str = week[0]
    end_date_str = week[1]
    data_week = generate_data_dict(file_path_data, start_date_str, end_date_str, n_houses, houses_pv, houses_bat, capacity_pv)

    # Run an instance of the model for a week
    instance = model_p2p(data_week)  # Replace with actual function

