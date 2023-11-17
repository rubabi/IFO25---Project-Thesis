clc
clear
RES = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\OneYear2021.xlsx",3,"B2162:H4345");
Dem = xlsread("C:\\Naser\\Projects\\BEYOND_P2P_PF\\Norwegian case\\DemandProfiles\\OneYear2021.xlsx",1,"B2162:H4345");
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\fval.mat')
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\fval_Nop2p.mat')
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\linsol.mat')
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\linsol_Nop2p.mat')
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\fval_nores.mat')
load('C:\Naser\Projects\BEYOND_P2P_PF\Norwegian case\Results\linsol_nores.mat')
%%
plot(fval_Nores,'g','Linewidth',1)
hold on
plot(fval_Nop2p,'r','Linewidth',1)
plot(fval,'b','Linewidth',1)
legend('No RES','No Community','Community')
xlabel('Day')
xlim([0 92])
ylabel('Cost [NOK]')   % The aggregated daily net cost of the houses

for i = 1:length(linsol)
    R(i) = sum(sum(RES((i-1)*24+1:i*24,:)));
    D(i) = sum(sum(Dem((i-1)*24+1:i*24,:)));
end
figure
plot(R)
hold on
plot(D)

%% Total cost
clc
sum(fval)
sum(fval_Nop2p)
sum(fval_Nores)
%% Average monthly cost 
clc
(sum(fval)/3)/7
(sum(fval_Nop2p)/3)/7
(sum(fval_Nores)/3)/7
%% Total grid consumption 
clc
for i=1:length(fval)
    Gh((i-1)*24+1:i*24,1)=sum(linsol(i).s.G,2);
    GhNC((i-1)*24+1:i*24,1)=sum(linsol_Nop2p(i).s.G,2);
    GhNRES((i-1)*24+1:i*24,1)=sum(linsol_Nores(i).s.G,2);
end
% figure
% plot(Gh,'b','Linewidth',1)
% hold on
% plot(GhNC,'r','Linewidth',1)
sum(Gh)
sum(GhNC)
sum(GhNRES)
%% Sold to the grid
clc
for i=1:length(fval)
    SG((i-1)*24+1:i*24,1)=sum(linsol(i).s.N,2);
    SGNC((i-1)*24+1:i*24,1)=sum(linsol_Nop2p(i).s.N,2);
end
% figure
% plot(SG,'b','Linewidth',1)
% hold on
% plot(SGNC,'r','Linewidth',1)
sum(SG)
sum(SGNC)
%% Self-consumption
clc
sum(sum(RES))-sum(SG)
sum(sum(RES))-sum(SGNC)
%% Total energy sharing
clc
for i=1:length(fval)
    X(i,1) = sum(sum(sum(linsol(i).s.Xp2p)));
end
sum(X)


