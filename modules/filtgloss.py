"""
created by JLY on 24 oct 2022. adapted from filterpugh.py
39-hour doodson filter. from hour to day.
Debugged on 13/VI/2023
"""
import numpy as np
import datetime
import math

def filtdaily2(df_input,taps):

    df = df_input.copy(deep=True)  # Jue added this, so we do not modify the entry df
    filtered = []
    HalfLenTaps=math.ceil(len(taps)/2)

    for t in range(0, len(df['data'])):
        if t - len(taps) < 0 or t + len(taps) > len(df['data']) or \
                (~np.isnan(df['data'][(t - len(taps)):(t + 1)])).sum() < (HalfLenTaps-1) or (~np.isnan(df['data'][t:(t + len(taps))])).sum() < (HalfLenTaps-1):
            filtered.append(np.NaN)
        else:
            summation = 0
            for m in range(1, len(taps)):
                summation = summation + taps[m] * (np.nan_to_num(df['data'][t + m]) + np.nan_to_num(df['data'][t - m]))
            filtered.append(round((taps[0] * np.nan_to_num(df['data'][t]) + summation) * 100) / 100)
    df['data'] = filtered
    df = df.resample('1D').apply(daily_resample)
    return df

def daily_resample(df):
    try:
        return df.loc[df.index.hour==12].values[0]
    except:
        return np.nan

def filtdoodson(df):
    # doodsonrules
    # create weight
    taps = [0] * 20
    for x in range(len(taps)):
        if x in [2, 3, 6, 7, 11, 12, 14, 17, 19]:
            taps[x] = 1 / 30
        elif x in [1, 4, 9]:
            taps[x] = 2 / 30
    taps = np.array(taps)
    return filtdaily2(df,taps)

def filtdemerliac(df):
    taps=np.array([768, 766, 762, 752, 738, 726, 704, 678, 658, 624, 586, 558, 512, 465, 435, 392, 351, 325,
    288, 253, 231, 200, 171, 153, 128, 105, 91, 72, 55, 45, 32, 21, 15, 8, 3, 1 ])/ 24576  #copied from sonel.org. Jue
    return filtdaily2(df,taps)



def filtmonthly(df):
    lastday_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    try:
        month1=df.index.month.values[0]
    except Exception as ex:
        monthly_mean=np.NaN
        return monthly_mean
    if len(df[~np.isnan(df)])>(lastday_month[month1-1]-15):
        monthly_mean=np.nanmean(df)
    else:
        monthly_mean=np.NaN
    return monthly_mean
