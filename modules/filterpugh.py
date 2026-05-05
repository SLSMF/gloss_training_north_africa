'''
filterhandler-module.
Created on 14 sep 2022.
Debugged on 13/VI/2023.
@author: AMG
'''
import utils.iofilehandler as iofilehandler
import datetime
import numpy as np
def filt(df_input,logger,c):#Jue changed df to df_input
    df=df_input.copy(deep=True)#Jue added this, so we do not modify the entry df
    logger.info('Filter - Pugh filterhandler >> started!')
    #pughrules
    taps = np.asarray(iofilehandler.filterwindow(c.pughtaps)).astype(np.float)
    filtered = []
    for t in range(0,len(df['data'])):
        #as we have resampled at exact 5min, we can say that we only compute at the exact 00minutes. if the sampling was not regular, we would have to compute at every 5min. Jue
        #
        if t-len(taps) < 0 or t+len(taps) > len(df['data']) or df.index[t].minute!=0 or \
                (~np.isnan(df['data'][(t-len(taps)):(t+1)])).sum()<54 or (~np.isnan(df['data'][t:(t+len(taps))])).sum()<54:
            filtered.append(np.NaN)
        else:
            summation = 0
            for m in range(1,len(taps)):
                summation = summation + taps[m] * (np.nan_to_num(df['data'][t+m]) + np.nan_to_num(df['data'][t-m]))#treat nans as zeroes. Jue. 7/nov/22
            filtered.append(round((taps[0] * np.nan_to_num(df['data'][t]) + summation) * 100) / 100)
    df['data'] = filtered
    df = df.resample('1H').first()
    return df
