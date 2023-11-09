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

def calculating_savings(instance, n_houses, start_date, end_date):

    # Creating the denominator - the case of no savings
    demand_df = pd.read_csv(directory('data')+'demand_Jan_365days.csv')
    demand_df = demand_df.iloc[:, :n_houses + 1]
    demand_df['Community demand'] = demand_df.iloc[:, 1:].sum(axis=1)

    prices_df = pd.read_csv(directory('data')+'dayahead_Jan_365days.csv')
    
    from_grid_df = pd.DataFrame()
    from_grid_df['time'] = demand_df['time'][:48]
    from_grid_df['Community grid expenditure'] = (demand_df['Community demand']) * prices_df['day ahead price (p/kWh)'][:48]
    
    no_savings = from_grid_df['Community grid expenditure'].sum()
    #------------------------------------------------------------------------------------------------------------------------------------------------

    # PV savings
    pv_prod_df = pd.read_csv(directory('data')+'solar_profile_scenarios_yearly.csv')
    pv_prod_df = pv_prod_df.iloc[:48, :3]
    pv_prod_df = pv_prod_df.rename(columns={pv_prod_df.columns[0]: 'time'})
    pv_prod_df['Community PV production'] = pv_prod_df.iloc[:, 1:].sum(axis=1)
    #------------------------------------------------------------------------------------------------------------------------------------------------

    # P2P savings
    X_p_dict = instance.X_p.get_values() # Collecting P2P transaction data
    X_p_df = pd.DataFrame.from_dict(X_p_dict, orient="index") # Converting to DF
    X_p_df.columns = ["X_p"] # Naming the dataframe
    X_p_df = X_p_df.reset_index()
    X_p_df[['Time', 'Household', "Peer"]] = pd.DataFrame(X_p_df['index'].tolist(), index=X_p_df.index) # Create a colun for each element
    X_p_df = X_p_df.drop(columns='index') # Eliminate the index column containing the tuple

    X = X_p_df['Time'].unique() # Get unique values for time, this will be the x-axis
    aggregated_df = pd.DataFrame()
    aggregated_df['time'] = X_p_df['Time'].unique()  

    for house in range(n_houses): # Get unique houses
        Y = X_p_df[X_p_df['Household'] == f'H{house + 1}']['X_p'].values # Transactions per house
        Y_aggregated = np.empty(len(X)) # Create an empty array to aggregate transactions per house per time step
        for time_step in range(int(len(Y)/n_houses)):
            Y_aggregated[time_step] = Y[time_step*n_houses:n_houses+time_step*n_houses].sum() # Aggregating 
        
        aggregated_df[f'H{house+1}'] = Y_aggregated # Adding the aggregation to a new column in the dataframe 
    
    P2P_savings_df = pd.DataFrame()
    P2P_savings_df['time'] = X_p_df['Time'].unique()  

    for house in range(n_houses):  # Summing the savings from P2P transactions
        P2P_savings_df[f'H{house+1}'] = aggregated_df[f'H{house+1}'][:48] * prices_df['day ahead price (p/kWh)'][:48]

    P2P_savings_df['Community savings'] = P2P_savings_df.iloc[:, 1:].sum(axis=1)
    P2P_savings = P2P_savings_df['Community savings'].sum()
    #------------------------------------------------------------------------------------------------------------------------------------------------

    # FFR savings
    T_FFR = [t for t in X if t.hour >= 22 or t.hour < 7]   

    Z_FFR = instance.Z_FFR.get_values()[None]
    FFR_price = 2.25 #[Pence/0.5kW] (half hour)
    FFR_savings = Z_FFR*FFR_price*len(T_FFR)
    #------------------------------------------------------------------------------------------------------------------------------------------------

    bill_reduction = (P2P_savings+FFR_savings)/no_savings

    return no_savings,bill_reduction,P2P_savings,FFR_savings