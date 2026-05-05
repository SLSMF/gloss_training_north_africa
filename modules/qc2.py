'''
qc-module
Created on 19 may. 2018
@author: JLY
debugged on 13/VI/2023
'''
import time
import utils.selenemath as smath
import numpy as np
import warnings
import scipy.stats as stats
import copy
def qc2(originaldf,max2,logger,c):
    logger.info('Quality control - qc module >> started!')
    t = time.time()
    warnings.simplefilter('ignore', np.RankWarning)
    df = originaldf.copy()
    badixs = []
    logger.debug('Original dataframe number of elements:' + str(len(df))) 
    df = df[df.quality != c.badqc]
    df = df[df.quality != c.nullqc]
    df_avg=np.nanmedian(df.data)

    if np.log10(abs(df_avg))> 5:
        df_avg_aux=np.nanmedian(df.data[np.log10(np.abs(df.data))<6])
        if np.isnan(df_avg_aux):
            pass
        else:
            df_avg=copy.deepcopy(df_avg_aux)
    q99 = np.nanpercentile(np.abs(df.data[np.log10(np.abs(df.data)) < 6] - df_avg), q=99)

    diff_data = df.data.diff(periods=1)
    diff_time = df.index.to_series().diff(periods=1).dt.total_seconds()/60 
    diff_time[diff_time>(24*60)]=60
    grad1 = diff_data / diff_time
    diff_data_rev = df.data.diff(periods=-1)
    diff_time_rev = df.index.to_series().diff(periods=-1).dt.total_seconds()/60 
    diff_time_rev[diff_time_rev>(24*60)]=-60
    grad1_rev = diff_data_rev / diff_time_rev
    logger.debug('Drop bad data. Dataframe number of elements:' + str(len(df))) 
    logger.debug('Quality control - TIME to clean bad data - qc module: ' + str(time.time() - t) + ' seconds')
    t = time.time()
    spikes1=False
    for ix in range(len(df.index.values)):
        data_aux = df.loc[df.index.values[ix], "data"]
        try:
            data1=data_aux[0]
        except:
            data1=data_aux
        if spikes1==False:
            if ((abs(grad1[ix]) > max2)  and (abs(data1-df_avg)>2*q99)):
                df.loc[df.index.values[ix],'quality'] = c.badqc
                badixs.append(df.index.values[ix])
                spikes1=True
        else:
            if ((abs(data1-df_avg)<3*q99) and (abs(grad1_rev[ix]) < max2) ):
                spikes1=False
            else:
                df.loc[df.index.values[ix], 'quality'] = c.badqc
                badixs.append(df.index.values[ix])


    logger.debug('Drop stuck data and out of range (max-min) data. Dataframe number of elements:' + str(len(df)))
    logger.debug('Quality control - TIME to check stuck values and out of range (max-min) values and clean bad data detected - qc module: ' + str(time.time() - t) + ' seconds')
    for badix in badixs:
        originaldf.loc[badix,'quality'] = c.badqc
        logger.info('Bad data detected: ' + str(badix))
    return originaldf
