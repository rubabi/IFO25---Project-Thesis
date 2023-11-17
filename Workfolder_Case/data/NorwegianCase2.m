clc
clear

Year = 1;  % 0 -> 2020, 1 -> 2021, 2 -> 2022

h1 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068222797.ods",Year+1,"B2162:B2881");  %Apr
h2 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068222919.ods",Year+1,"B2162:B2881");
h3 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068252350.ods",Year+1,"B2:B553");
h4 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068252398.ods",Year+1,"B2162:B2881");
h5 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068253326.ods",Year+1,"B2162:B2881");
h6 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068253449.ods",Year+1,"B2162:B2881");
% h7 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068741601.ods",Year+1);
h8 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\707057500068978168.ods",Year+1,"B2162:B2881");
% 
% S1 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\Solar_RenewablesNinja\\Solar1kwCap.csv");
% S2 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\Solar_RenewablesNinja\\Solar2kwCap.csv");
% S3 = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\Solar_RenewablesNinja\\Solar3kwCap.csv");

%%
plot([h1 h2 h3 h4 h5 h6 h7 h8])
hold on
plot(S,'g','linewidth',0.5)



