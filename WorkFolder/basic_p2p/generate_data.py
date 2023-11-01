import pandas as pd
from pyomo.environ import *
import pytz

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
    p_spot_df = pd.read_csv(file_path_data + r"dayahead_Jan_365days.csv", index_col=0,
                            parse_dates=[0], date_format=date_format_str)  # to make sure the date is read properly
    p_spot_df.index = p_spot_df.index.to_pydatetime() # convert to a datetime format required for the model
    p_spot_df = p_spot_df[["day ahead price (p/kWh)"]]  # get only price in pences/kWh
    p_spot_df_ = p_spot_df[(p_spot_df.index >= start_date) & (p_spot_df.index < end_date)]
    # Convert the dataframe P_spot_df_ to dictionary for data input for the function model_p2p()
    p_spot = p_spot_df_.to_dict()

    # Get demand
    p_demand_df = pd.read_csv(file_path_data + r"demand_Jan_365days.csv", index_col=0,
                              parse_dates=[0], date_format=date_format_str)  # to make sure the date is read properly
    p_demand_df.index = p_demand_df.index.to_pydatetime() # convert to a datetime format required for the model
    p_demand_df = p_demand_df[list_houses]  # Filter based on the houses selected
    p_demand_df.index = p_spot_df.index  # Change index from 2013 to 2019. The weeks of the days are the rest, so no more operations are needed
    p_demand_df_ = p_demand_df[(p_demand_df.index >= start_date) & (p_demand_df.index < end_date)]
    p_demand_df_ = p_demand_df_.stack()  # Set time and household as index
    # Convert the dataframe to dictionary
    p_demand = p_demand_df_.to_dict()

    # Get solar profiles, we assume the PV profile is the same for each house given that they are located close to each other
    res_df = pd.read_csv(file_path_data + r"solar_profile_scenarios_yearly.csv", index_col=0,
                        parse_dates=[0], date_format=date_format_str)
    res_df.index = res_df.index.to_pydatetime() # convert to a datetime format required for the model
    scn = "1"
    res_df = res_df[[scn]]  # Select just one scenario, the data is prepared for several scenarios
    res_df_ = res_df[(res_df.index >= start_date) & (res_df.index < end_date)]
    # Convert the dataframe to dictionary
    res = res_df_.to_dict()

    # Set T
    list_T = p_spot_df_.index.to_list()

    # Parameter PV_cap
    res_cap = {f"H{key}":capacity_pv[i] for i, key in enumerate(houses_pv)}

    # Scalars (single value parameters)
    alpha = 1.5  # charging rate 2.5 kW -> 1.25 kWh/hour at constant rate
    beta = 1.5  # discharging rate 2.5 kW -> 1.25 kWh/hour at constant rate
    eta_charge = 0.96  # Charging efficiency
    eta_discharge = 0.96  # Discharging efficiency
    eta_diff = 0 # Diffusion efficiency
    eta_P2P = 1 - 0.076  # Losses (assume a loss of 7.6% through the local network, Luth)
    k = 0 # Energy initially available in flexible asset
    smax = 4  # capacity batteries [kWh] # It can also be changes to be similar to parameter PV_cap where you specify the capacity of each battery
    smin = smax * 0.2  # minimum state of charge of batteries at all times
    s_init = smax * 0.5  # initial state of charge of the battery
    #FFR related---------------------------------------------------------------------------------------------------------------------
    p_FFR = -450 #[Pence/kWh]

    # Construct data dictionary
    data = {  # always start with None and then dictionary
        None: {  # names of the keys equal to the name of the parameteres in the model
            'H': {None: list_houses},  # providing data for set H
            'H_pv': {None: list_houses_pv},  # providing data for set H_pv
            "H_bat": {None: list_houses_bat},  # providing data for set H_bat
            "T": {None: list_T},  # providing datetime for set T
            # Parameters
            "Dem": p_demand,
            "res": res[scn],
            "res_cap": res_cap,
            'p_spot': p_spot['day ahead price (p/kWh)'],
            # Scalars
            "alpha": {None: alpha},
            "beta": {None: beta},
            "eta_charge": {None: eta_charge},
            "eta_discharge": {None: eta_discharge},
            "eta_P2P": {None: eta_P2P},
            "smax": {None: smax},
            "smin": {None: smin},
            "s_init": {None: s_init},
            # Prices
            "p_FFR": {None: p_FFR},
        }}

    return data