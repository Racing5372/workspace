#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 12:20:55 2016

@author: tsz
"""
from __future__ import division

import numpy as np
import gurobipy as gp
import matplotlib.pyplot as plt

import twoElements
import testcases as tc

model = gp.Model("tc12")

# Definition of time horizon
times_per_hour = 15
timesteps = 24 * 60 * times_per_hour # 60 days
timesteps_day = int(24 * times_per_hour)

# Zero inputs
window   = np.zeros(timesteps)
windowIndoorSurface     = np.zeros(timesteps)
extWallIndoorSurface    = np.zeros(timesteps)
intWallIndoorSurface    = np.zeros(timesteps)

# Initial Values
T_start = 273.15 + 22

# Variable inputs
intGainsConv = np.zeros(timesteps_day)
intGainsRad  = np.zeros(timesteps_day)
for q in range(int(7*timesteps_day/24), int(17*timesteps_day/24)):
    intGainsConv[q] = 80 + 200
    intGainsRad [q] = 80
intGainsConv = np.tile(intGainsConv, 60)
intGainsRad  = np.tile(intGainsRad , 60)

solarRad_raw = np.loadtxt("inputs/case12_q_sol.csv", usecols=(1,))
solarRad = solarRad_raw[0:24]
solarRad[solarRad > 100] = solarRad[solarRad > 100] * 0.15
solarRad_adj = np.repeat(solarRad, times_per_hour)
solRad = np.array([np.tile(solarRad_adj, 60)]).T

t_outside_raw = np.loadtxt("inputs/case12_t_amb.csv", delimiter=",")
t_outside = ([t_outside_raw[2*i,1] for i in range(24)])
t_outside_adj = np.repeat(t_outside, times_per_hour)
Tv = np.tile(t_outside_adj, 60)

extWall = Tv

# VentRate --> incoming volume flow rate in m3/s
ventRate = np.zeros(timesteps_day) + 100 / 3600
for q in range(int(7*timesteps_day/24), int(17*timesteps_day/24)):
    ventRate[q] = 50 / 3600
ventRate = np.tile(ventRate, 60)

# Load constant house parameters
params = tc.get_house_data(timesteps, case=12)

# Ventilation and air parameters
ports = {}
ports["Tv"] = Tv
ports["ventRate"] = ventRate
ports["rhoair"] = 1.19 # kg/m3
ports["cair"] = 1007 #
ports["heaterCooler"] = False
ports["setAirTemp"] = False

# Load initial values into the model
Tair = model.addVar(vtype="C", name="Tair_start", lb=-100.)
Tow  = model.addVar(vtype="C", name="Tow_start", lb=-100.)
Tiw  = model.addVar(vtype="C", name="Tiw_start", lb=-100.)
model.update()
model.addConstr(Tair == T_start)
model.addConstr(Tow == T_start)
model.addConstr(Tiw == T_start)
model.update()

# deactivate console (gurobi) output
model.params.outputFlag = 0.

# Calculate indoor air temperature
T_air, Q_HC, Q_iw, Q_ow = twoElements.twoElements(params, solRad, window, extWall, 
                                                  windowIndoorSurface, 
                                                  extWallIndoorSurface,
                                                  intWallIndoorSurface, 
                                                  intGainsConv, intGainsRad, ports,
                                                  model,
                                                  dt=int(3600/times_per_hour))

# Compute averaged results
T_air_c = T_air - 273.15
T_air_mean = np.array([np.mean(T_air_c[i*times_per_hour:(i+1)*times_per_hour]) for i in range(24*60)])

T_air_1 = T_air_mean[0:24]
T_air_10 = T_air_mean[216:240]
T_air_60 = T_air_mean[1416:1440]

# Load reference results    
(T_air_ref_1, T_air_ref_10, T_air_ref_60) = tc.load_res("inputs/case12_res.csv")
T_air_ref_1 = T_air_ref_1[:,0]
T_air_ref_10 = T_air_ref_10[:,0]
T_air_ref_60 = T_air_ref_60[:,0]


# Plot comparisons
def plot_result(res, ref, title="Results day 1"):
    plt.figure()
    ax_top = plt.subplot(211)
    plt.plot(ref, label="Reference", color="black", linestyle="--")
    plt.plot(res, label="Simulation", color="blue", linestyle="-")
    plt.legend()
    plt.ylabel("Temperature in degC")
    
    plt.title(title)

    plt.subplot(212, sharex=ax_top)
    plt.plot(res-ref, label="Ref. - Sim.")
    plt.legend()
    plt.ylabel("Temperature difference in K")
    plt.xticks([4*i for i in range(7)])
    plt.xlim([1,24])
    plt.xlabel("Time in h")

plot_result(T_air_1, T_air_ref_1, "Results day 1")
plot_result(T_air_10, T_air_ref_10, "Results day 10")
plot_result(T_air_60, T_air_ref_60, "Results day 60")

print("Max. deviation day 1: " + str(np.max(np.abs(T_air_1 - T_air_ref_1))))
print("Max. deviation day 10: " + str(np.max(np.abs(T_air_10 - T_air_ref_10))))
print("Max. deviation day 60: " + str(np.max(np.abs(T_air_60 - T_air_ref_60))))