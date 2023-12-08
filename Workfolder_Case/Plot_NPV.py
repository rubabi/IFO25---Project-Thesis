import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import matplotlib.ticker as ticker
from directories_P2P import directory

dpi_number = 300
figsize = (8, 4)
start_plot_at = 0
stop_plot_at = 8

filepath = "c:/Users/jakob/Downloads/NPV.xlsx"

#read the file and store it in a dataframe
df = pd.read_excel(filepath, sheet_name="Plot", header=1, index_col=0)

#make every column to a numpy array
r = np.array(df.r)[start_plot_at:stop_plot_at]
NoFFR_PV_Bat = np.array(df.NoFFR_PV_Bat)[start_plot_at:stop_plot_at]
Profil_PV_Bat = np.array(df.Profil_PV_Bat)[start_plot_at:stop_plot_at]
Flex_PV_Bat = np.array(df.Flex_PV_Bat)[start_plot_at:stop_plot_at]
NoFFR_Bat = np.array(df.NoFFR_Bat)[start_plot_at:stop_plot_at]
Profil_Bat = np.array(df.Profil_Bat)[start_plot_at:stop_plot_at]
Flex_Bat = np.array(df.Flex_Bat)[start_plot_at:stop_plot_at]


#Setup the plot. Colors should be 01377D, 009DD1, 97E7F5, 7ED348, 26B170

#plot the PV_Bat cases
plt.figure(figsize=figsize)
plt.plot(r, NoFFR_PV_Bat, label="No FFR", color="#97E7F5")
plt.plot(r, Profil_PV_Bat, label="Profil" , color="#009DD1")
plt.plot(r, Flex_PV_Bat, label="Flex", color="#01377D")
plt.xlabel("r")
plt.grid()
formatter = ticker.FuncFormatter(lambda x, p: format(int(x), ' '))
plt.gca().yaxis.set_major_formatter(formatter)
formatter = ticker.FuncFormatter(lambda x, pos: '{:.0f}%'.format(x*100))
plt.gca().xaxis.set_major_formatter(formatter)
plt.ylabel("NPV [NOK]")
plt.legend(loc="upper right")
plt.savefig("C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/Workfolder_Case/results/NPV_PV_Bat.png", dpi = dpi_number)
plt.show()

#plot the Bat cases
plt.figure(figsize=figsize)
plt.plot(r, NoFFR_Bat, label="No FFR", color="#97E7F5")
plt.plot(r, Profil_Bat, label="Profil" , color="#009DD1")
plt.plot(r, Flex_Bat, label="Flex", color="#01377D")
plt.xlabel("r")
plt.grid()
formatter = ticker.FuncFormatter(lambda x, p: format(int(x), ' '))
plt.gca().yaxis.set_major_formatter(formatter)
formatter = ticker.FuncFormatter(lambda x, pos: '{:.0f}%'.format(x*100))
plt.gca().xaxis.set_major_formatter(formatter)
plt.ylabel("NPV [NOK]")
plt.legend(loc="upper right")
plt.savefig("C:/Users/jakob/Documents/Masteroppgave/IFO25---Project-Thesis/Workfolder_Case/results/NPV_Bat.png", dpi = dpi_number)
plt.show()


