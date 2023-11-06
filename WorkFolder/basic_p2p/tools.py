import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

def calculating_savings(instance):
    # Creating the denominator - the case of no savings
    no_savings = 1

    # Finding savings from P2P
    X_p_dict = instance.X_p.get_values() # Collecting P2P transaction data
    X_p_df = pd.DataFrame.from_dict(X_p_dict, orient="index") # Converting to DF
    X_p_df.columns = ["X_p"] # Naming the dataframe
    X_p_df = X_p_df.reset_index()
    X_p_df[['Time', 'Household', "Peer"]] = pd.DataFrame(X_p_df['index'].tolist(), index=X_p_df.index) # Create a colun for each element
    X_p_df = X_p_df.drop(columns='index') # Eliminate the index column containing the tuple
    P2P_savings = X_p_df['X_p'].sum() # Summing the savings from P2P transactions

    bill_reduction = P2P_savings/no_savings

    return bill_reduction, P2P_savings, no_savings