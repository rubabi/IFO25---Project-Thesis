import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from directories_P2P import directory
from generate_data import generate_data_dict
from model_components_P2P import model_p2p

def print_non_zero_shadow_prices(instance, Constraint):
        #Show shadow prices
    print("Shadow prices:")
    for c in instance.component_objects(Constraint, active=True):
        print ("Constraint",c)
        for index in c:
            #only print shadow prices that are not zero
            if instance.dual[c[index]] != 0:
                print ("   ", index, instance.dual[c[index]])
        print ("")

def print_non_binding_constraints(instance, Constraint):
    print("Non-binding constraints:")
    for c in instance.component_objects(Constraint, active=True):
        #print constraint if all shadow prices are zero
        if all(instance.dual[c[index]] == 0 for index in c):
            print ("   ",c)
    print ("")

def print_binding_constraints(instance, Constraint):
    print("Binding constraints:")
    for c in instance.component_objects(Constraint, active=True):
        #print constraint if all shadow prices are zero
        if any(instance.dual[c[index]] != 0 for index in c):
            print ("   ",c)
    print ("")

def P2P_exports(instance, file_path_results, n_houses, plot): # Printing function template sort of
    # If you want to see the results, you can call the result as dictionary
    X_p_dict = instance.X_p.get_values()
    # Then you can convert it to dataframe
    X_p_df = pd.DataFrame.from_dict(X_p_dict, orient="index")
    X_p_df.columns = ["X_p"] # set a name for the dataframe
    # In this case, you have a tuple as index, you need to separate them so that you can perform analysis
    # First, set the index as a column
    X_p_df = X_p_df.reset_index()
    # Then, create one column for each element
    X_p_df[['Time', 'Household', "Peer"]] = pd.DataFrame(X_p_df['index'].tolist(), index=X_p_df.index)
    # Eliminate the index column containing the tuple
    X_p_df = X_p_df.drop(columns='index')
    # Set the columns as index again
    X_p_df = X_p_df.set_index(["Time", "Household", "Peer"])

    # Then you can plot the results or save it as excel
    X_p_df.to_csv(file_path_results + "X_p.csv")

    P2P_volume = X_p_df['X_p'].sum()

    if plot:
        fig, ax = plt.subplots(figsize=(12,7))

        X = X_p_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis

        # Aggregate the transactions to align shapes
        for house in X_p_df.index.get_level_values(1).unique():
            Y = X_p_df[X_p_df.index.get_level_values(1) == house].values
            Y_aggregated = np.empty(len(X))
            for time_step in range(int(len(Y)/n_houses)):
                Y_aggregated[time_step]=Y[time_step*n_houses:n_houses+time_step*n_houses].sum()
            ax.plot(X, Y_aggregated, label=f"{house}")

        ax.set_ylabel("P2P export (kWh)")
        ax.legend()

        fig.tight_layout()
        plt.show()

    return P2P_volume

def export_volume(instance):
    G_export_df = pd.DataFrame.from_dict(instance.G_export.get_values(), orient='index', columns=['G_export'])
    G_export_df.reset_index(inplace=True)
    G_export_df[['Time', 'Household']] = pd.DataFrame(G_export_df['index'].tolist(), index=G_export_df.index)
    G_export_df.drop(columns='index', inplace=True)
    G_export_df.set_index('Time', inplace=True)
    G_export_df = G_export_df[['Household', 'G_export']]

    return G_export_df['G_export'].sum()

def calculating_savings(instance, start_date, end_date):
    
    start_date = pd.to_datetime(start_date, format='%Y-%m-%d')
    end_date = pd.to_datetime(end_date, format='%Y-%m-%d')

    #$ Base case (no savings)
    demand_df = pd.DataFrame(list(instance.dem.items()), columns=['index', 'Demand'])
    demand_df[['Time', 'Household']] = pd.DataFrame(demand_df['index'].tolist(), index=demand_df.index)
    demand_df.set_index('Time', inplace=True)
    demand_df = demand_df[['Household', 'Demand']]

    prices_df = pd.DataFrame(list(instance.p_spot.items()), columns=['Time', 'Day ahead price (NOK/kWh)'])
    prices_df.set_index('Time', inplace=True)

    from_grid_df = pd.DataFrame(index=demand_df.index)
    from_grid_df = from_grid_df[~from_grid_df.index.duplicated(keep='first')]
    from_grid_df['Demand'] = demand_df.groupby(demand_df.index).sum()['Demand']
    from_grid_df['Day ahead price (NOK/kWh)'] = prices_df['Day ahead price (NOK/kWh)']
    from_grid_df['Community grid expenditure'] = from_grid_df['Demand'] * (from_grid_df['Day ahead price (NOK/kWh)']+instance.p_retail.value)

    peak_power = from_grid_df['Demand'].resample('M').max()

    naked_case = from_grid_df['Community grid expenditure'].sum()+peak_power.sum()*instance.p_peak[start_date.month]
    #------------------------------------------------------------------------------------------------------------------------------------------------

    #$ P2P savings
    X_p_df = pd.DataFrame.from_dict(instance.X_p.get_values(), orient='index', columns=['X_p'])
    X_p_df.reset_index(inplace=True)
    X_p_df[['Time', 'Household', 'Peer']] = pd.DataFrame(X_p_df['index'].tolist(), index=X_p_df.index)
    X_p_df.drop(columns='index', inplace=True)
    X_p_df.set_index('Time', inplace=True)
    X_p_df = X_p_df[['Household', 'Peer', 'X_p']]

    X_p_df_aggregated = pd.DataFrame()
    X_p_df_aggregated['X_p_aggregated'] = X_p_df.groupby(['Time', 'Peer']).sum()['X_p']
    X_p_df_aggregated = X_p_df_aggregated.join(prices_df)
    X_p_df_aggregated['P2P savings'] = X_p_df_aggregated['X_p_aggregated'] * (from_grid_df['Day ahead price (NOK/kWh)']+instance.p_retail.value)

    P2P_savings = X_p_df_aggregated['P2P savings'].sum()
    #------------------------------------------------------------------------------------------------------------------------------------------------

    #$ Peak cost savings
    G_import_df = pd.DataFrame.from_dict(instance.G_import.get_values(), orient='index', columns=['G_import'])
    G_import_df.reset_index(inplace=True)
    G_import_df[['Time', 'Household']] = pd.DataFrame(G_import_df['index'].tolist(), index=G_import_df.index)
    G_import_df.drop(columns='index', inplace=True)
    G_import_df.set_index('Time', inplace=True)
    G_import_df = G_import_df[['Household', 'G_import']]

    G_import_df_aggregated = pd.DataFrame()
    G_import_df_aggregated['G_import_aggregated'] = G_import_df.groupby(['Time']).sum()['G_import']
    peak_power_case = G_import_df_aggregated['G_import_aggregated'].resample('M').max()

    Peak_savings = (peak_power.sum()-peak_power_case.sum())*instance.p_peak[start_date.month]
    #------------------------------------------------------------------------------------------------------------------------------------------------

    #$ Grid export savings
    G_export_df = pd.DataFrame.from_dict(instance.G_export.get_values(), orient='index', columns=['G_export'])
    G_export_df.reset_index(inplace=True)
    G_export_df[['Time', 'Household']] = pd.DataFrame(G_export_df['index'].tolist(), index=G_export_df.index)
    G_export_df.drop(columns='index', inplace=True)
    G_export_df.set_index('Time', inplace=True)
    G_export_df = G_export_df[['Household', 'G_export']]

    G_export_df_aggregated = pd.DataFrame()
    G_export_df_aggregated['G_export_aggregated'] = G_export_df.groupby(['Time']).sum()['G_export']
    G_export_df_aggregated['G_export gain'] = G_export_df_aggregated['G_export_aggregated']*(from_grid_df['Day ahead price (NOK/kWh)'])

    G_export_savings = G_export_df_aggregated['G_export gain'].sum()

    #$ FFR savings
    T_FFR = list(instance.T_FFR)

    Z_FFR = instance.Z_FFR.get_values()[None]

    p_FFR = instance.p_FFR.value
    FFR_savings = Z_FFR*p_FFR*len(T_FFR)
    #------------------------------------------------------------------------------------------------------------------------------------------------

    return naked_case,P2P_savings,FFR_savings,Peak_savings,G_export_savings

def plot_state_of_charge(instance):
    # If you want to see the results, you can call the result as dictionary
    S_dict = instance.S.get_values()
    # Then you can convert it to dataframe
    S_df = pd.DataFrame.from_dict(S_dict, orient="index")
    S_df.columns = ["S"] # set a name for the dataframe
    # In this case, you have a tuple as index, you need to separate them so that you can perform analysis
    # First, set the index as a column
    S_df = S_df.reset_index()
    # Then, create one column for each element
    S_df[['Time', 'Household']] = pd.DataFrame(S_df['index'].tolist(), index=S_df.index)
    # Eliminate the index column containing the tuple
    S_df = S_df.drop(columns='index')
    # Set the columns as index again
    S_df = S_df.set_index(["Time", "Household"])

    # Then you can plot the results or save it as excel
    S_df.to_csv(directory('results') + "S.csv")

    fig, ax = plt.subplots(figsize=(12,7))

    X = S_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis

    # Aggregate the transactions to align shapes
    for house in S_df.index.get_level_values(1).unique():
        Y = S_df[S_df.index.get_level_values(1) == house].values
        ax.plot(X, Y, label=f"{house}")

    ax.set_ylabel("State of charge (kWh)")
    ax.legend()

    fig.tight_layout()
    plt.show()

def overview_plot(instance):
    #$ Set up subplot 
    plt.subplots_adjust(hspace=0)
    plt.rcParams['font.size'] = 7
    plt.rcParams['axes.grid'] = True

    G_import_dict = instance.G_import.get_values()
    C_dict = instance.C.get_values()
    D_dict = instance.D.get_values()
    S_dict = instance.S.get_values()
    p_spot_dict = instance.p_spot
    dem_dict = instance.dem
    res_dict = instance.res
    R_charge_dict = instance.R_FFR_charge.get_values()
    R_discharge_dict = instance.R_FFR_discharge.get_values()

    G_import_df = pd.DataFrame.from_dict(G_import_dict, orient="index")
    C_df = pd.DataFrame.from_dict(C_dict, orient="index")
    D_df = pd.DataFrame.from_dict(D_dict, orient="index")
    S_df = pd.DataFrame.from_dict(S_dict, orient="index")
    p_spot_df = pd.DataFrame.from_dict(p_spot_dict, orient="index")
    dem_df = pd.DataFrame.from_dict(dem_dict, orient="index")
    res_df = pd.DataFrame.from_dict(res_dict, orient="index")
    R_charge_df = pd.DataFrame.from_dict(R_charge_dict, orient="index")
    R_discharge_df = pd.DataFrame.from_dict(R_discharge_dict, orient="index")


    #$ Placing the plots in the plane
    n = 9 #number of subplots
    plot_spot = plt.subplot2grid((n,1), (0,0))
    plot_demand = plt.subplot2grid((n,1), (1,0), sharex=plot_spot)
    plot_res = plt.subplot2grid((n,1), (2,0), sharex=plot_spot)
    plot_import = plt.subplot2grid((n,1), (3,0), sharex=plot_spot)
    plot_charge = plt.subplot2grid((n,1), (4,0), sharex=plot_spot)
    plot_discharge = plt.subplot2grid((n,1), (5,0), sharex=plot_spot)
    plot_state_of_charge = plt.subplot2grid((n,1), (6,0), sharex=plot_spot)
    plot_R_charge = plt.subplot2grid((n,1), (7,0), sharex=plot_spot)
    plot_R_discharge = plt.subplot2grid((n,1), (8,0), sharex=plot_spot)

    #$ Plotting the spot price
    X = p_spot_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    Y = p_spot_df.values
    plot_spot.plot(X, Y, label="Spot price")
    plot_spot.set_ylabel("Spot Price [p/kWh]")

    #$ Plotting the demand
    dem_df.index = pd.MultiIndex.from_tuples(dem_df.index)
    X = dem_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in dem_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = dem_df.xs(house, level=1).values # Get values for the current house
        plot_demand.plot(X, Y, label=f"{house}")
    plot_demand.set_ylabel("Dem [kWh]")
    plot_demand.legend(loc='upper right')

    #$ Plotting the production
    X = res_df.index # Time will be the x-axis
    Y = res_df.values # Total production values
    plot_res.plot(X, Y, label="Production")
    plot_res.set_ylabel("Res [kWh]")

    #$ Plotting the import
    G_import_df.index = pd.MultiIndex.from_tuples(G_import_df.index)
    X = G_import_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in G_import_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = G_import_df.xs(house, level=1).values # Get values for the current house
        plot_import.plot(X, Y, label=f"{house}")
    plot_import.set_ylabel("$G^{import}$ [kWh]")
    plot_import.legend(loc='upper right')

    #$ Plotting the charge
    C_df.index = pd.MultiIndex.from_tuples(C_df.index)
    X = C_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in C_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = C_df.xs(house, level=1).values
        plot_charge.plot(X, Y, label=f"{house}")
    plot_charge.set_ylabel("C [kWh]]")
    plot_charge.legend(loc='upper right')

    #$ Plotting the discharge
    D_df.index = pd.MultiIndex.from_tuples(D_df.index)
    X = D_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in D_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = D_df.xs(house, level=1).values
        plot_discharge.plot(X, Y, label=f"{house}")
    plot_discharge.set_ylabel("D [kWh]")
    plot_discharge.legend(loc='upper right')

    #$ Plotting the state of charge
    S_df.index = pd.MultiIndex.from_tuples(S_df.index)
    X = S_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in S_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = S_df.xs(house, level=1).values
        plot_state_of_charge.plot(X, Y, label=f"{house}")
    plot_state_of_charge.set_ylabel("S [kWh]")
    plot_state_of_charge.legend(loc='upper right')

    #$ Plotting the FFR charge
    R_charge_df.index = pd.MultiIndex.from_tuples(R_charge_df.index)
    X = R_charge_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in R_charge_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = R_charge_df.xs(house, level=1).values
        plot_R_charge.plot(X, Y, label=f"{house}")
    plot_R_charge.set_ylabel("$R^{+}$ [kWh]")
    plot_R_charge.legend(loc='upper right')

    #$ Plotting the FFR discharge
    R_discharge_df.index = pd.MultiIndex.from_tuples(R_discharge_df.index)
    X = R_discharge_df.index.get_level_values(0).unique() # Get unique values for time, this will be the x-axis
    for house in R_discharge_df.index.get_level_values(1).unique(): # Get unique house identifiers
        Y = R_discharge_df.xs(house, level=1).values
        plot_R_discharge.plot(X, Y, label=f"{house}")
    plot_R_discharge.set_ylabel("$R^{-}$ [kWh]")
    plot_R_discharge.legend(loc='upper right')

    #plt.tight_layout()
    plt.show()

#Function to print the costs from the object function
def print_costs(instance):
    from pyomo.environ import value
    spot_cost = sum(value(instance.G_import[t, h]) * instance.p_spot[t] for t in instance.T for h in instance.H)
    retail_cost = sum(value(instance.G_import[t, h]) * instance.p_retail for t in instance.T for h in instance.H)
    peak_cost = sum(value(instance.G_peak[m]) * instance.p_peak[m] for m in instance.M)
    export_cost = -sum(value(instance.G_export[t, h]) * instance.p_spot[t] * (1 - instance.psi) for t in instance.T for h in instance.H)
    FFR_cost = -value(instance.Z_FFR) * instance.p_FFR * len(instance.T_FFR)

    # Create a dictionary with the costs
    costs = {
        'Spot Cost': spot_cost,
        'Retail Cost': retail_cost,
        'Peak Cost': peak_cost,
        'Export Cost': export_cost,
        'FFR Cost': FFR_cost,
        'Total Cost': spot_cost + retail_cost + peak_cost + export_cost + FFR_cost
    }

    # Create a DataFrame from the dictionary
    costs_df = pd.DataFrame(list(costs.items()), columns=['Cost Type', 'Value'])
    costs_df['Value'] = costs_df['Value'].apply(lambda x: f"{x:.2f} NOK")
    # Print the DataFrame without the index
    print(costs_df.to_string(index=False))

#Function to print the costs from the object function to a latex table
def costs_to_latex(instance):
    from pyomo.environ import value
    spot_cost = sum(value(instance.G_import[t, h]) * instance.p_spot[t] for t in instance.T for h in instance.H)
    retail_cost = sum(value(instance.G_import[t, h]) * instance.p_retail for t in instance.T for h in instance.H)
    peak_cost = sum(value(instance.G_peak[m]) * instance.p_peak[m] for m in instance.M)
    export_cost = -sum(value(instance.G_export[t, h]) * instance.p_spot[t] * (1 - instance.psi) for t in instance.T for h in instance.H)
    FFR_cost = -value(instance.Z_FFR) * instance.p_FFR * len(instance.T_FFR)

    # Create a dictionary with the costs
    costs = {
        'Spot Cost': spot_cost,
        'Retail Cost': retail_cost,
        'Peak Cost': peak_cost,
        'Export Cost': export_cost,
        'FFR Cost': FFR_cost,
        'Total Cost': spot_cost + retail_cost + peak_cost + export_cost + FFR_cost
    }

    # Create a DataFrame from the dictionary
    costs_df = pd.DataFrame(list(costs.items()), columns=['Cost Type', 'Value'])
    costs_df['Value'] = costs_df['Value'].apply(lambda x: f"{x:.2f} NOK")
    print(costs_df.to_latex(index=False, label="tab:costs", caption="[Caption here]"))

#Function to print all variables to excel
def write_to_excel(instance, file_path_results, FFR_type, P2P_switch, PV_switch, Battery_switch, Export_to_grid_switch, start_date, end_date):
    # If you want to see the results, you can call the result as dictionary
    G_import_dict = instance.G_import.get_values()
    C_dict = instance.C.get_values()
    D_dict = instance.D.get_values()
    S_dict = instance.S.get_values()
    R_charge_dict = instance.R_FFR_charge.get_values()
    R_discharge_dict = instance.R_FFR_discharge.get_values()

    G_import_df = pd.DataFrame.from_dict(G_import_dict, orient="index")
    C_df = pd.DataFrame.from_dict(C_dict, orient="index")
    D_df = pd.DataFrame.from_dict(D_dict, orient="index")
    S_df = pd.DataFrame.from_dict(S_dict, orient="index")
    R_charge_df = pd.DataFrame.from_dict(R_charge_dict, orient="index")
    R_discharge_df = pd.DataFrame.from_dict(R_discharge_dict, orient="index")

    # Make a dataframe that contains P2P, PV, battery and export settings, start date and end date, to use for information sheet
    settings_dict = {"FFR Type":str(FFR_type), "P2P": str(P2P_switch), "PV": str(PV_switch), "Battery": str(Battery_switch), "Export": str(Export_to_grid_switch), "Start date": str(start_date), "End date": str(end_date)}
    settings_df = pd.DataFrame.from_dict(settings_dict, orient="index")
    
    # Write the DataFrames to Excel
    from datetime import datetime
    file_path_name = file_path_results + 'Results_' + str(FFR_type) + '_P2P_' + str(P2P_switch) + '_PV_' + str(PV_switch) + '_Battery_' + str(Battery_switch) + '_Export_' + str(Export_to_grid_switch) + '_' + datetime.now().strftime("%Y-%m-%d %H-%M") + '.xlsx'

    with pd.ExcelWriter(file_path_name) as writer:
        settings_df.to_excel(writer, sheet_name='Settings', index=True)
        G_import_df.to_excel(writer, sheet_name='G_import')
        C_df.to_excel(writer, sheet_name='C')
        D_df.to_excel(writer, sheet_name='D')
        S_df.to_excel(writer, sheet_name='S')
        R_charge_df.to_excel(writer, sheet_name='R_charge')
        R_discharge_df.to_excel(writer, sheet_name='R_discharge')
