import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from directories_P2P import directory
from generate_data import generate_data_dict

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

def print_P2P_exports(instance, file_path_results, n_houses): # Printing function template sort of
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

def calculating_savings(instance, start_date, end_date):
    
    start_date = pd.to_datetime(start_date, format='%Y-%m-%d')
    end_date = pd.to_datetime(end_date, format='%Y-%m-%d')
    days = (end_date - start_date).days

    n_houses = len(instance.H)
    time_steps_per_day = int(len(list(instance.T.data()))/days)

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
    from_grid_df['Community grid expenditure'] = from_grid_df['Demand'] * from_grid_df['Day ahead price (NOK/kWh)']

    no_savings = from_grid_df['Community grid expenditure'].sum()
    #------------------------------------------------------------------------------------------------------------------------------------------------

    #$ P2P savings
    X_p_df = pd.DataFrame.from_dict(instance.X_p.get_values(), orient='index', columns=['X_p'])
    X_p_df.reset_index(inplace=True)
    X_p_df[['Time', 'Household', 'Peer']] = pd.DataFrame(X_p_df['index'].tolist(), index=X_p_df.index)
    X_p_df.drop(columns='index', inplace=True)
    X_p_df.set_index('Time', inplace=True)
    X_p_df = X_p_df[['Household', 'Peer', 'X_p']]

    P2P_savings = 0
    #------------------------------------------------------------------------------------------------------------------------------------------------

    #$ FFR savings
    T_FFR = instance.T_FFR

    Z_FFR = instance.Z_FFR.get_values()[None]

    p_FFR = instance.p_FFR.value
    FFR_savings = Z_FFR*p_FFR*len(T_FFR)
    #------------------------------------------------------------------------------------------------------------------------------------------------

    bill_reduction = (P2P_savings+FFR_savings)/no_savings

    return no_savings,bill_reduction,P2P_savings,FFR_savings


# function for plotting the state of charge of the batteries
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

# function for plotting
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