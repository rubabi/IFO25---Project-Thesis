import pandas as pd
from pyomo.environ import *
import pytz
import os
import numpy as np

def generate_data_dict(file_path_data, start_date_str, end_date_str, houses_pv, houses_bat, capacity_pv, FFR_type, PV_switch, Battery_switch):
    #list_houses = [f"H{i}" for i in range(1, n_houses + 1)]
    list_houses = ["H97", "H19", "H50", "H98", "H26", "H49", "H68"] #According to file aprTaug2021
    list_houses.sort(key=lambda x: int(x[1:]))
    list_houses_pv = [f"H{i}" for i in houses_pv]
    list_houses_bat = [f"H{i}" for i in houses_bat]

    # transforming dates to align with data
    utc_tz = pytz.UTC  # just used to ensure matching the dates with the index
    start_date = pd.to_datetime(start_date_str, format=r'%Y-%m-%d').tz_localize(utc_tz)
    end_date = pd.to_datetime(end_date_str, format=r'%Y-%m-%d').tz_localize(utc_tz)

    #$ Get spot prices
    date_format_str = '%Y-%m-%d %H:%M:%S%z'  # '2019-12-06 14:00:00+00:00' format
    #p_spot_df = pd.read_csv(file_path_data + r"Prices_updated.csv", index_col=0,
                            #parse_dates=[0], date_format=date_format_str)  # to make sure the date is read properly
    p_spot_df = pd.read_csv(os.path.join(file_path_data, r"Prices_updated_17.11.csv"), index_col=0,
                            parse_dates=[0], date_format=date_format_str)
    p_spot_df.index = p_spot_df.index.to_pydatetime() # convert to a datetime format required for the model
    p_spot_df = p_spot_df[["NOK/kWh"]]  # get only price in NOK/kWh
    p_spot_df_ = p_spot_df[(p_spot_df.index >= start_date) & (p_spot_df.index < end_date)]
    # Convert the dataframe P_spot_df_ to dictionary for data input for the function model_p2p()
    p_spot = p_spot_df_.to_dict()

    #$ Get demand
    dem_df = pd.read_excel(os.path.join(file_path_data,r"DemandProfiles/aprTaug2021.xlsx"), index_col=0, parse_dates=[0])
    #dem_df.index = dem_df.index.to_pydatetime() # convert to a datetime format required for the model
    dem_df = dem_df[list_houses]  # Filter based on the houses selected
    # Now apply the conversion to datetime without the timezone information
    dem_df.index = dem_df.index.str.rsplit('[', n=1).str[0] # remove the timezone information
    dem_df.index = pd.to_datetime(dem_df.index, utc=True) # convert to a datetime format required for the model
    dem_df_ = dem_df[(dem_df.index >= start_date) & (dem_df.index < end_date)] # Filter based on the dates selected
    dem_df_ = dem_df_.stack()  # Set time and household as index
    # Convert the dataframe to dictionary
    dem = dem_df_.to_dict()


    #$ Get solar profiles, we assume the PV profile is the same for each house given that they are located close to each other
    res_df = pd.read_excel(os.path.join(file_path_data, r"DemandProfiles/aprTaug2021.xlsx"), sheet_name = "RESprofiles", index_col=0,
             parse_dates=[0], date_format=date_format_str)
    res_df.index = pd.to_datetime(res_df.index, utc=True) # convert to a datetime format required for the model
    res_df_ = res_df[(res_df.index >= start_date) & (res_df.index < end_date)]
    scn = "5kw" # Select one scenario, the data is prepared for several scenarios. Needs to be changed to be more general
    res_df_ = res_df_[[scn]]  # Select just one scenario, the data is prepared for several scenarios
    
    # If PV_switch is False, set all PV production to 0
    if not PV_switch:
        res_df_[scn] = 0
    
    # Convert the dataframe to dictionary
    res = res_df_.to_dict()
    # Parameter PV_cap
    res_cap = {f"H{key}":capacity_pv[i] for i, key in enumerate(houses_pv)}

    # Set T
    #index_date = dem_df_.index.get_level_values(0)
    #list_T = index_date.to_list()
    list_T = p_spot_df_.index.to_list()

    # Set M
    index_date = p_spot_df_.index
    list_M = list(np.unique([t.month for t in index_date])) # Retrieves the month from each element in the index and filters unique values
    list_T_M = [(t, t.month) for t in index_date] # list creating tuple of the T set and the M set

    #! Manual input data --------------------------------------------------------------------------------------------------------------------
    # Scalars (single value parameters)
    eta_charge = 0.96  # Charging efficiency
    eta_discharge = 0.96  # Discharging efficiency
    eta_diff = 0.99 # Diffusion efficiency #! Change?
    eta_P2P = 1 - 0.076  # Losses (assume a loss of 7.6% through the local network, Luth)
    psi = 0.05  # Marginal loss-rate when feeding into the grid
    if Battery_switch:
        alpha = 5  # Charging capacity continuous rate Tesla home battery
        beta = 5 # Discharging capacity continuous rate Tesla home battery
        smax = 13.5  # Tesla powerwall capacity [kWh] # It can also be changes to be similar to parameter PV_cap where you specify the capacity of each battery
    else:
        alpha = 0
        beta = 0
        smax = 0
    smin = smax * 0.2  # minimum state of charge of batteries at all times
    s_init = smax * 0.5  # initial state of charge of the battery
    x_limit = 100  # Grid export limit [kW]

    p_peak = {m: 60 for m in list_M}
    p_retail = 0.45 # Retail price of electricity, grid tariff [NOK/kWh]
    #!---------------------------------------------------------------------------------------------------------------------------------------

    # FFR type
    if FFR_type == "Flex":
        p_FFR = 0.45 
        list_T_FFR = list_T
    elif FFR_type == "Profil":
        p_FFR = 0.15
        list_T_FFR = [t for t in list_T if t.hour >= 22 or t.hour < 7]
    elif FFR_type == "No FFR":
        p_FFR = 0
        list_T_FFR = list_T

    # Construct data dictionary
    data = {  # always start with None and then dictionary
        None: {  # names of the keys equal to the name of the parameteres in the model
            'H': {None: list_houses},  # providing data for set H
            'H_pv': {None: list_houses_pv},  # providing data for set H_pv
            "H_bat": {None: list_houses_bat},  # providing data for set H_bat
            "T": {None: list_T},  # providing datetime for set T
            "T_FFR": {None: list_T_FFR},  # providing datetime for set T_FFR
            # Months and Grid RAQUEL
            "M": {None: list_M},
            "T_M": {None: list_T_M},
            # Parameters
            "dem": dem,
            "res": res[scn],
            "res_cap": res_cap,
            # Prices
            'p_spot': p_spot["NOK/kWh"],
            "p_FFR": {None: p_FFR},
            "p_peak": p_peak,
            "p_retail": {None: p_retail},
            # Scalars
            "alpha": {None: alpha},
            "beta": {None: beta},
            "eta_charge": {None: eta_charge},
            "eta_discharge": {None: eta_discharge},
            "eta_diff": {None: eta_diff},
            "eta_P2P": {None: eta_P2P},
            "psi": {None: psi},
            "smax": {None: smax},
            "smin": {None: smin},
            "s_init": {None: s_init},
            "x_limit": {None: x_limit},
        }}
    
    return data