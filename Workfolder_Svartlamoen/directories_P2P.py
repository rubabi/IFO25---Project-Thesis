import getpass

# Defining usernames to run code from multiple computers
current_user = getpass.getuser()
JK = "jakob"
OH = "olehermanimset"
RI = "rubab"

def directory(folder):
    
    if current_user == JK:
        if folder == "data":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder_Svartlamoen/data/Norwegian case/"
        elif folder == "results":
            return "C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/WorkFolder_Svartlamoen/results/"
        else:
            print('Invalid directory input')
    elif current_user == OH:
        if folder == "data":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder_Svartlamoen/data/Norwegian case/'
        elif folder == "results":
            return '/Users/olehermanimset/Library/CloudStorage/OneDrive-NTNU/9. Semester/Project Thesis/IFO25---Project-Thesis/WorkFolder_Svartlamoen/results/'
        else:
            print('Invalid directory input')
    elif current_user == RI:
        if folder == "data":
            return 'C:/Users/rubab/Desktop/NTNU/Semester/11Semester/TIO4550/KodingIFO25/IFO25---Project-Thesis/WorkFolder_Svartlamoen/data/Norwegian case/'
        elif folder == "results":
            return 'C:/Users/rubab/Desktop/NTNU/Semester/11Semester/TIO4550/KodingIFO25/IFO25---Project-Thesis/WorkFolder_Svartlamoen/results/'
        else:
            print('Invalid directory input')
    else:
        print(f"Sorry, {current_user}, you are not the intended user.")