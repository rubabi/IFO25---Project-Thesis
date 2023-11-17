import getpass

# Defining usernames to run code from multiple computers
current_user = getpass.getuser()
JK = "jakob"
OH = "olehermanimset"
RI = "rubab"

def directory(folder):
    
    if current_user == JK:
        if folder == "Test case":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/data/Norwegian_case/"
        elif folder == "results":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/results/"
        else:
            print('Invalid directory input')
    elif current_user == OH:
        if folder == "Test case":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/data/Norwegian_case/'
        elif folder == "results":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/results/'
        else:
            print('Invalid directory input')
    elif current_user == RI:
        if folder == "Test case":
            return 'C:/Users/rubab/Desktop/NTNU/Semester/11Semester/TIO4550/KodingIFO25/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/data/Norwegian_case/'
        elif folder == "results":
            return 'C:/Users/rubab/Desktop/NTNU/Semester/11Semester/TIO4550/KodingIFO25/IFO25---Project-Thesis/WorkFolder_Svartlamoen/basic_p2p/results/'
        else:
            print('Invalid directory input')
    else:
        print(f"Sorry, {current_user}, you are not the intended user.")