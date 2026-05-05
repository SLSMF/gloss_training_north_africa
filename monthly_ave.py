#debugged on 17 apr. 2026

import pandas as pd
import modules.filtgloss as filtgloss
import numpy as np
import os
import sys

def monthly_ave(hourlyfiltered,stationid):
    #compute monthly average value
    #pack for compute monthly avrage, call compute daily average and compute monthly average (calls fiterdoodson)
    #compute surge
    # make time sampling homogeneous, and equal to 60min
    ts_rng = pd.date_range(hourlyfiltered.index[0].strftime('%Y-%m-%d %H:%M:%S'),
                           hourlyfiltered.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
                           freq='60Min')
    ts_df0 = pd.DataFrame(index=ts_rng)
    hourlyfiltered2 = pd.merge(ts_df0, hourlyfiltered, left_index=True, right_index=True)

    # interpolate
    hourlyfiltered2["data"] = hourlyfiltered2["data"].resample("H").interpolate(limit=4)#changed from 24h. 18032026
    #reorganize dataframe
    hourlyfiltered2=hourlyfiltered2.drop(columns=['quality'])
    #compute daily mean with filter
    dailyfiltered = filtgloss.filtdoodson(hourlyfiltered2)#have index and column 'data'
    dailyfiltered=dailyfiltered.replace('None',np.nan).dropna(subset=['data'])#edited 19032026
    #compute and save monthly mean
    monthlyfiltered = dailyfiltered.resample("MS").apply(filtgloss.filtmonthly)#edited 13/I/2025
    mean_M=np.nanmean(monthlyfiltered.data)
    monthlyfiltered["data"]=monthlyfiltered.apply(lambda x: (x["data"]-mean_M),axis=1)#monthlyfiltered has index and column='data'
    monthlyfiltered=monthlyfiltered.replace('None',np.nan).dropna(subset=['data'])#added 19032026
    return monthlyfiltered,dailyfiltered
