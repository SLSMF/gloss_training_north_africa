import modules.interpolation as inter
#Debugged on 13/VI/2023

constit = ['SA', 'SSA', 'MSM', 'MM', 'MSF', 'MF', 'ALP1', '2Q1', 'SIG1', 'Q1', 'RHO1', 'O1', 'TAU1', 'BET1', 'NO1',
           'CHI1', 'PI1', 'P1', 'S1', 'K1', 'PSI1', 'PHI1', 'THE1', 'J1', 'SO1', 'OO1', 'UPS1', 'OQ2', 'EPS2', '2N2',
           'MU2', 'N2', 'NU2', 'H1', 'M2', 'H2', 'MKS2', 'LDA2', 'L2', 'T2', 'S2', 'R2', 'K2', 'MSN2', 'ETA2', 'MO3',
           'M3', 'SO3', 'MK3', 'SK3', 'MN4', 'M4', 'SN4', 'MS4', 'MK4', 'S4', 'SK4', '2MK5', '2SK5', '2MN6', 'M6',
           '2MS6', '2MK6', '2SM6', 'MSK6', '3MK7', 'M8']

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import utide
import pickle
from scipy.signal import butter,filtfilt
import configuration.constants as c

folder_harm="configuration/harmonics"

ini_month, end_month = 1, 12
month_lst = ['{0:02d}'.format(j) for j in list(range(ini_month, end_month + 1))]

cutoff_hours = 15 
fs = 1 / 3600  
cutoff = 1 / (3600 * cutoff_hours) 
nyq = 0.5 * fs  
order = 9  
def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def tide_reconstruct(df_input, target_station,constit_out=None):
    df=df_input.copy(deep=True)
    df['TIDE']=np.nan
    df['RES'] = np.nan
    df["RES_noAstroTide"]=np.nan
    df_h=df.resample('H').mean()
    if constit_out is None:
        constit_out = constit
    list_years = ['{}'.format(i) for i in list(df[~np.isnan(df.data)].index.year.unique())]
    with open(os.path.join(folder_harm,str(target_station)+"_harm_all.pkl"),"rb") as harm_all:
        coef_tot=pickle.load(harm_all)
    for year in list_years:
        df_year_h = df_h[df_h.index.year == int(year)] 
        if (year in coef_tot.keys()) and (coef_tot[year] != None):
            coef_tot2 = coef_tot[year]
        else:
            coef_tot2=None
            skip_year=1
            while coef_tot2==None and skip_year<4:
                try:
                    coef_tot2=coef_tot[str(int(year)-skip_year)]
                except:
                    try:
                        coef_tot2=coef_tot[str(int(year)+skip_year)]
                    except:
                        pass
                skip_year+=1
        for month1 in month_lst:
            df_month_h=df_year_h[df_year_h.index.month==int(month1)]
            time1_h = mdates.date2num(df_month_h.index)
            if coef_tot2!=None and len(df_month_h)>0:
                tide_h = np.array(
                    (utide.reconstruct(time1_h, coef_tot2, min_SNR=0, verbose=True, constit=constit_out)).h)*1000
                res_h=df_month_h['data']-tide_h
                df_month_h['RES']=res_h
            else:
                df_month_h['RES'] = np.nan  
            df_month_h = df_month_h[~df_month_h.index.duplicated(keep='first')]
            df_h.update(df_month_h)
    df_h["RES"] = pd.to_numeric(df_h["RES"], errors='coerce').astype("float64")
    df['RES']=inter.back2original(df_h['RES'],df_h.index,df.index,c)
    int_tot=np.nanmedian(df.index.to_series().diff(periods=1).dt.total_seconds() / 60)
    df["TIDE"] = df.apply(lambda x: x["data"] - x["RES"], axis=1)  
    if int_tot == 60:
        sig_filtered=butter_lowpass_filter(df["RES"].fillna(0),cutoff,fs,5)
        sig_filtered[np.isnan(df["RES"])]=np.nan
        df["RES_noAstroTide"]=sig_filtered
    else:
        df["RES_noAstroTide"]=df["RES"]

    return df


