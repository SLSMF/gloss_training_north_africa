'''
qc-module
Created on 19 may. 2018
@author: AMG
Debugged on 15 apr. 2026
'''
import time
import utils.selenemath as smath
import numpy as np
import warnings
from scipy.interpolate import CubicSpline,splrep,splev 
from scipy.stats import kurtosis, variation

def qc(originaldf,nsigma,winsize,splinedegree,stucklimit,max,min,logger,c):
    logger.info('Quality control - qc module >> started!')
    t = time.time()
    warnings.simplefilter('ignore', np.RankWarning)
    df = originaldf.copy(deep=True)
    badixs = []
    logger.debug('Original dataframe number of elements:' + str(len(df))) 
    df = df[df.quality != c.badqc]
    df = df[df.quality != c.nullqc]
    logger.debug('Drop bad data. Dataframe number of elements:' + str(len(df))) 
    logger.debug('Quality control - TIME to clean bad data - qc module: ' + str(time.time() - t) + ' seconds')
    t = time.time()
    #stuck test and range (max-min) test
    range1 = abs(max - min) / 3  
    diff_data=df.data.diff(periods=1)
    stuckcount2=1;
    for ix in range(len(df.index.values)):
        if abs(diff_data[ix])==0:
            stuckcount2+=1
            if stuckcount2 == stucklimit:
                df.loc[df.index.values[(ix-stucklimit+1):(ix+1)],'quality'] = c.badqc
                badixs.append(df.index.values[(ix-stucklimit+1):(ix+1)])
            elif stuckcount2 > stucklimit:
                df.loc[df.index.values[ix],'quality'] = c.badqc
                badixs.append(df.index.values[ix])
        else:
            stuckcount2 = 1
    #max-min 
    cond_lim=(df.data > max) | (df.data < min)
    df.loc[df.index.values[cond_lim],'quality'] = c.badqc
    badixs.append(df.index.values[cond_lim])
    df = df[df.quality != c.badqc]
    logger.debug('Drop stuck data and out of range (max-min) data. Dataframe number of elements:' + str(len(df)))
    logger.debug('Quality control - TIME to check stuck values and out of range (max-min) values and clean bad data detected - qc module: ' + str(time.time() - t) + ' seconds')
    spikedetected = True
    iter = 0
    while spikedetected and iter < c.maxiter:
        df = df[df.quality != c.badqc]
        diff_data = np.diff(df.data,n=1)
        logger.debug('Spike iteration. Dataframe number of elements:' + str(len(df))) 
        spikedetected = False
        t = time.time()
        for ix in range(len(df.index.values)):
            if (ix < winsize/2):
                ini=0
                end=winsize-1
                winix = ix
            elif (ix > len(df.index) - winsize/2):
                ini=len(df.index)-winsize
                end=len(df.index)-1
                winix = (winsize-1)-(end-ix+1)
            else:
                ini = int(ix - winsize/2)
                end = int(ix + winsize/2)
                winix = int(winsize/2)
            windata = df['data'].values[ini:end]
            win_diffdata=diff_data[ini:end]
            if np.any(np.abs(win_diffdata)>np.max([100,range1/50])):
                winx = df.index.values[ini:end].astype(float)
                splinefit = np.polyfit(winx, windata, splinedegree)
                splinedata = np.polyval(splinefit,winx)
                rmse = np.nanmax([smath.rmse(splinedata, np.array(windata)),range1/10,50])
                if (abs(splinedata[winix]-df['data'][ix]) >= nsigma*rmse):
                    df.loc[df.index.values[ix],'quality'] = c.badqc
                    badixs.append(df.index.values[ix])
                    spikedetected = True
        logger.debug('Quality control - TIME to spike test loop - qc module: ' + str(time.time() - t) + ' seconds')
        iter=iter+1
    for badix in badixs:
        originaldf.loc[badix,'quality'] = c.badqc
        logger.info('Bad data detected: ' + str(badix))
    return originaldf
