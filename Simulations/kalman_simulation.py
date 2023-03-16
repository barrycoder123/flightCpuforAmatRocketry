#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 12:46:07 2023

@author: zrummler

PURPOSE: Runs a Kalman Filtering simulation with Draper's test data

SEE KALMAN.PY FOR DOCUMENTATION ON THE KALMAN FILTERING IMPLEMENTATION

"""
import importlib

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append('../Flight Algorithms')
sys.path.append('../Data Collection')
sys.path.append('../Test Data')

import kalman as kf
import earth_model as em
import file_data_collection as fdc
from misc import plotDataAndError

importlib.reload(kf)
importlib.reload(em)
importlib.reload(fdc)

if __name__ == "__main__":
    '''
    1. Imports test data
    2. Runs Kalman Filtering on the data
    3. Compares results of Kalman Filter to truth data (run the code and see plots)
    '''
    print("Kalman Filtering Simulation")

    # Import and format data
    print("Opening file for truth data...")
    data = pd.read_csv("../Test Data/traj_raster_30mins_20221115_160156.csv").to_numpy()
    PVA_truth = data[:, 1:11].T

    # Holds our results, for plotting
    print("Initializing arrays...")
    dc = fdc.FileDataCollector()
    num_points = dc.num_points
    PVA_est = np.zeros((10, num_points))
    PHist = np.zeros((9, 9, num_points))  # to store the covariance at each step
    
    # Initialize state vectors and matrices
    x = dc.get_first_position()
    q_true = dc.get_first_quaternion()
    ekf = kf.EKF(x, q_true)

    # ========================== filter ==========================
    print("Running Extended Kalman Filter...")
    i = 0
    while i < num_points:

        # Read IMU
        accel, gyro, dt = dc.get_next_imu_reading()
        z_imu = np.concatenate((accel, gyro))
        
        # Prediction
        ekf.predict(z_imu, dt)

        # Read GPS and barometer -- these return None if no new data
        baro = dc.get_next_barometer_reading()
        lla, dt = dc.get_next_gps_reading()
        #lla = None
        #print(lla)

        # Update
        baro = None
        #baro = baro[:1] # try just one barometer before all three
        ekf.update(lla, baro, sigma_gps=5, sigma_baro=10) # try variance = 10

        # save the data
        PVA_est[:6, i] = ekf.x[:6]  # store ECEF position and velocity
        PVA_est[6:10, i] = ekf.q_e2b
        PHist[:, :, i] = ekf.P  # store the covariance
        i += 1

    # ========================== plotting ==========================
    print("Plotting results...")

    tplot = np.arange(PVA_est.shape[1])
    plotDataAndError(PVA_est[:3, :], PVA_truth[:3, :], tplot, subx0=True)
    plotDataAndError(PVA_est[3:6, :], PVA_truth[3:6, :], tplot, name='Velocity', subx0=True)
    #plotDataAndError(PVA_est[:3, ::10], PVA_truth[:3, ::10], tplot[::10], subx0=True)
    plotDataAndError(PVA_est[6:10, ::10], PVA_truth[6:10, ::10], tplot[::10], axes=['A', 'B', 'C', 'D'], name='Quaternion', unit=None)

    # fig, axs = plt.subplots(3, 1, sharex=True, figsize=(11, 8))
    # for i, (ax, lab) in enumerate(zip(axs, ['X', 'Y', 'Z'])):
    #     ax.plot(PVA_truth[i, :] - PVA_truth[i, 0], label='Truth')
    #     ax.plot(PVA_est[i, :] - PVA_truth[i, 0], label='Estimate')
    #     ax.set_title(f"{lab} ECEF Position (minus start)\nWITH KALMAN FILTERING (GPS + IMU)")
    #     ax.legend()
    #     ax.grid(True)
    # plt.tight_layout()
    plt.show()  # needed to display the figures
