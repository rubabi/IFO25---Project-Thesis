import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import matplotlib.ticker as ticker

dpi_number = 300
figsize = (8, 4)
colors = ['#97E7F5', '#009DD1', '#01377D']
fontsize = 8

base_case = 15644.05
df_savings = pd.DataFrame(
    data=[[8473.03, 10370.85, 25553.99], 
          [978.27, 3148.74, 19552.68], 
          [5875.66, 5875.66, 5875.66]],
    columns=["No FFR", "Profil", "Flex"],
    index=["PVs and Batteries", "Only Batteries", "Only PVs"]
)

# plot the savings as a bar chart
df_savings_vs_basecase = df_savings / base_case * 100

fig, ax = plt.subplots()
df_savings_vs_basecase.plot(kind='bar', ax=ax, color=colors)
ax.set_ylabel('Savings compared to the base case [%]', fontsize=fontsize)
plt.xticks(rotation='horizontal')
ax.set_ylim(0, 180)
ax.axhline(100, color='#26B170', linestyle='--') 
ax.annotate('', xy=(2, 110), xytext=(2, 100), arrowprops=dict(arrowstyle='->', color='black'))
ax.text(1.6, 116, 'Earning profits instead\nof incurring costs', color='#000000', va='center', ha='left',
        bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.5'), fontsize=fontsize)

# Add percentages on top of the bars
for p in ax.patches:
    width = p.get_width()
    height = p.get_height()
    x, y = p.get_xy() 
    ax.annotate(f'{height:.0f}%', (x + width/2, y + height+2), ha='center', fontsize=fontsize)

plt.show()

# Plot the ratios of PV off, B on against PV on, B on
# Barchart
plt.figure(figsize=figsize)
plt.bar(df_savings.columns, df_savings.iloc[0], label="Savings due to PVs", color="#01377D", width = 0.5)
plt.bar(df_savings.columns, df_savings.iloc[1], label="Savings due to Batteries", color="#009DD1", width = 0.5)
formatter = ticker.FuncFormatter(lambda x, p: format(int(x), ' '))
plt.gca().yaxis.set_major_formatter(formatter)
plt.ylabel("Cost savings [NOK]", fontsize=fontsize)
plt.legend(loc="upper left")

# Lineplot
ax2 = plt.gca().twinx()
ax2.plot(df_savings.columns, (df_savings.iloc[1]/df_savings.iloc[0])*100, label="Savings due to Batteries [%]", color="#7ED348")
ax2.set_ylabel("Savings due to batteries [%]", fontsize=fontsize)
ax2.legend(loc="upper right")
ax2.set_ylim(0, 100)

# Write each percent on the line
for i, v in enumerate((df_savings.iloc[1]/df_savings.iloc[0])*100):
    ax2.text(i, v, str(round(v, 1))+"%", color="#000000", ha="center", va="bottom", 
             bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.5'), fontsize=fontsize)
plt.show()