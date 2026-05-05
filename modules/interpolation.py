'''
interpolation-module
Created on 19 may. 2018
@author: AMG
Updated 13/VI/2023
'''
import numpy as np
import pandas as pd

def resampleandinterpolate(df,mininterval,c):
    dfreturn = df.resample(str(mininterval) + 'T').mean()
    dfreturn['quality'] = dfreturn['quality'].fillna(c.interqc)
    dfreturn = dfreturn.interpolate()
    return dfreturn
def interpolate(originaldf,intervalinterpolate,mininterval,logger,config,c):
    logger.info('Interpolation - qc interpolation >> started!')
    #properties
    maxgapinminutes = int(config['interpolation']['maxgapinminutes']) # Max allowed gap in minutes
    subsamplingmethod = config['interpolation']['subsamplingmethod'] # mean, first(default)
    #logic
    df = originaldf.copy()
    if intervalinterpolate == None:
        intervalinterpolate = str(mininterval) + 'T'
    else:
        intervalinterpolate = str(intervalinterpolate) + 'T'
    df = df[df.quality != c.badqc]
    targetdf = df[df.quality == c.badqc]
    ini=0
    for ix in range(1,len(df.index.values)):
            if df.index.values[ix] - df.index.values[ix-1] > np.timedelta64(maxgapinminutes, 'm'):
                end = ix
                targetdf = pd.concat([targetdf,resampleandinterpolate(df[ini:end], mininterval, c)],axis=0,join="outer")
                ini = ix
    end = len(df.index.values)
    targetdf = pd.concat([targetdf,resampleandinterpolate(df[ini:end], mininterval,c)],axis=0,join="outer",sort=True)
    targetdf = targetdf.resample(str(mininterval) + 'T').mean()
    targetdf['quality'] = targetdf['quality'].fillna(c.nullqc)
    if subsamplingmethod == 'mean':
        targetdf = targetdf.resample(intervalinterpolate).mean()
    else:
        targetdf = targetdf.resample(intervalinterpolate).first()
    targetdf['quality'] = targetdf['quality'].fillna(c.interqc).interpolate()
    targetdf=leavegaps(originaldf,targetdf,maxgapinminutes,c)
    targetdf = targetdf.drop(columns='quality', axis=1)
    try:
        targetdf = targetdf.drop(columns='quality_old', axis=1)
    except:
        pass
    return targetdf

def back2original(array_hourly,time_hourly,time_original,c):
    dataframe_hourly={}
    dataframe_hourly["data"]=array_hourly
    dataframe_hourly["quality"]=1
    dataframe_hourly=pd.DataFrame(dataframe_hourly,index=time_hourly)
    dataframe_hourly.loc[np.isnan(dataframe_hourly.data),"quality"]=c.nullqc
    dataframe_original=pd.DataFrame([],index=time_original)
    joint_dataframe=dataframe_original.join(dataframe_hourly)
    joint_dataframe["quality"]=joint_dataframe["quality"].fillna(c.interqc)
    dataframe_original_interpolated_aux=joint_dataframe.interpolate()
    dataframe_original_interpolated = np.array((leavegaps(dataframe_hourly, dataframe_original_interpolated_aux, 60, c)).data)
    return dataframe_original_interpolated


def leavegaps(originaldf,targetdf,maxgapinminutes,c):
    originaldf.loc[np.isnan(originaldf.data),"quality"]=c.nullqc 
    originaldf_aux = pd.concat([originaldf.iloc[[0]], originaldf[originaldf.quality == 1], originaldf.iloc[[-1]]],
                               axis=0, join="outer", sort=True)

    diff_originalB = originaldf_aux.index.to_series().diff(periods=1).dt.total_seconds() / 60  
    diff_original = originaldf_aux.index.to_series().diff(periods=-1).dt.total_seconds() / 60  
    gap_end = originaldf_aux[(diff_originalB > maxgapinminutes)].index
    gap_ini = originaldf_aux[(diff_original < -maxgapinminutes)].index
    if len(gap_ini)>0:
        for ii in range(len(gap_ini)):
            targetdf.loc[(targetdf.index>gap_ini[ii])&(targetdf.index<gap_end[ii]),'quality']=c.nullqc
            targetdf.loc[(targetdf.index>gap_ini[ii])&(targetdf.index<gap_end[ii]),'data']=np.nan
    return targetdf
