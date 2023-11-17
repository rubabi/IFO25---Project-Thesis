clc
clear

EndUserID = ["707057500068222797", "707057500068222919", "707057500068252350", "707057500068252398", "707057500068253326", "707057500068253449", "707057500068741601", "707057500068978168"];
MONTH=["april"];
Year=[2021];

i=2;
fix="C:/Naser/Projects/BEYOND_P2P_PF/Norwegian case/Data Beyond Norway/Data Beyond Norway/";
add=strcat(fix,EndUserID(i),"/","meteringvalues-mp-",EndUserID(i),"-consumption-",MONTH,"-",string(Year),".csv");

readmatrix(add)


% "C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Data Beyond Norway\Data Beyond Norway\707057500068222797\meteringvalues-mp-707057500068222797-consumption-april-2020.csv"
% "C:/Naser/Projects/BEYOND_P2P_PF/Norwegian case/Data Beyond Norway/Data Beyond Norway/707057500068222797/meteringvalues-mp-707057500068222797-consumption-april-2021.csv"
% 
% 
% xlsread()

