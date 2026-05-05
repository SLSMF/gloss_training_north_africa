'''
selene
Created on 5 jun. 2018
@author: AMG
debugged on 17 apr. 2026
python selene.py [target_station]
'''
import os
base_dir=os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
folder_harm=os.path.join(base_dir,"configuration","harmonics")
import sys
import time
import logging
import configparser
import json
import pandas as pd
import numpy as np
import configuration.constants as c
import utils.iofilehandler as iofilehandler
import utils.dataframe as dataframe
import utils.compute_surge as compute_surge
import modules.qc as qc
import modules.qc2 as qc2
import modules.interpolation as inter
import pickle
import warnings
from numba.core.errors import NumbaDeprecationWarning, NumbaWarning
# Suppress the noisy Numba and Runtime warnings
warnings.simplefilter('ignore', category=NumbaDeprecationWarning)
warnings.simplefilter('ignore', category=NumbaWarning)
warnings.simplefilter('ignore', category=RuntimeWarning)


stationid =  sys.argv[1]
initime = time.time()
#log
extralogatt = {'station':stationid}
logger = logging.getLogger('selene')
fh = logging.FileHandler(c.logfile)
fh.setFormatter(logging.Formatter('%(asctime)s %(station)s %(levelname)s %(message)s'))
fh.setFormatter(logging.Formatter('%(asctime)s %(station)s %(levelname)s %(message)s'))
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)
logger = logging.LoggerAdapter(logger, extralogatt)
#config
t = time.time()
logger.info('SELENE application >> started!')
config = configparser.ConfigParser()
config.read(c.configini)
logger.info('Config file: ' + c.configini + ' read!')
with open(c.stationsfile) as f:
    stations = json.load(f)
logger.info('Stations json file: ' + c.stationsfile + ' loaded!')
logger.debug('TIME to read config and json files: ' + str(time.time() - t) + ' seconds')
if stationid not in stations:
    logger.error('Station id ' + stationid + ' not set in stations.json. SELENE terminated!')
    sys.exit()
try:
    t = time.time()

    originaldf = iofilehandler.txtfile2dataframe(stations[stationid]['seriesfile'],stations[stationid]['seriesseparator'],list(map(int,stations[stationid]['seriesdatecolumns'].split(','))),stations[stationid]['seriesdateformat'],stations[stationid]['seriesvaluecolumn'],stations[stationid]['seriesqccolumn'],logger)
    t = time.time()
    if originaldf.empty:
        logger.info('Empty file for station ' + stationid)
        sys.exit()
    foremanstartdate = pd.to_datetime(originaldf.index.values[0])
    foremanenddate = pd.to_datetime(originaldf.index.values[-1])
    logger.debug('TIME to create dataframe from series file: ' + str(time.time() - t) + ' seconds')
    t = time.time()
    if originaldf[(originaldf.quality != 4) & (originaldf.quality != 9)].empty == True:
        logger.info('All data in station ' + stationid + ' is wrong or null (qc = 4 or qc = 9)')
        sys.exit()

    if stations[stationid]["data_mode"]=="R":
        originaldf=originaldf.rename(columns={"quality": "quality_old"})
        originaldf["quality"]=1
    elif stations[stationid]["data_mode"]=="D" or stations[stationid]["data_mode"]=="M":
        originaldf["quality_old"]=originaldf["quality"].copy(deep=True)
        originaldf=originaldf[["data","quality_old","quality"]]


    maxgapinminutes = int(config['interpolation']['maxgapinminutes']) 
    originalmininterval = max(np.nanmedian(originaldf.index[-1000:].to_series().diff(periods=1).dt.total_seconds() / 60),1)  
    originalmininterval_nonans = max(np.nanmedian(
        originaldf[~np.isnan(originaldf.data)].index.to_series().diff(periods=1).dt.total_seconds() / 60),1) 
    first_track_sampling = max(np.nanmedian(originaldf.index[:1000].to_series().diff(periods=1).dt.total_seconds() / 60),1)  

    try:
        originaldfwithflags_aux = qc.qc(originaldf,stations[stationid]['qc_level_nsigma'],stations[stationid]['qc_level_winsize'],stations[stationid]['qc_level_splinedegree'],stations[stationid]['qc_stucklimit'],stations[stationid]['maxlevel'],stations[stationid]['minlevel'],logger,c)
        originaldfwithflags = qc2.qc2(originaldfwithflags_aux,stations[stationid]['max2'], logger, c)
    except:
        originaldfwithflags=originaldf.copy(deep=True)
    logger.info('TIME to check quality - qc module: ' + str(time.time() - t) + ' seconds')
    t = time.time()
    #ORIGINAL SAMPLING SURGE
    try:
        with open(os.path.join(folder_harm, str(stationid) + "_harm_all.pkl"), "rb") as harm_all:
            coef_ave_all = pickle.load(harm_all)
    except:
        coef_ave_all=None
    if coef_ave_all:
        # ORIGINAL SAMPLING INTERPOLATED DATA
        originaldfinterpolated = inter.interpolate(originaldfwithflags, None, originalmininterval, logger, config, c)
        tidesurgedf=compute_surge.compute_tidesurge(originaldfinterpolated,stationid)[["RES_noAstroTide","quality"]].rename(columns={"RES_noAstroTide":"data"})
        logger.debug('TIME to calculate tide surge - tidesurge module: ' + str(time.time() - t) + ' seconds')
        t = time.time()
        tidesurgedfwithflags=qc.qc(tidesurgedf,stations[stationid]['qc_surge_nsigma'],stations[stationid]['qc_surge_winsize'],
                                   stations[stationid]['qc_surge_splinedegree'],stations[stationid]['qc_stucklimit'],stations[stationid]['maxsurge'],
                                   stations[stationid]['minsurge'],logger,c)
        tidesurgebadflags=tidesurgedfwithflags[tidesurgedfwithflags.quality==c.badqc]
        if not tidesurgebadflags.empty:
            for ix in tidesurgebadflags.index.values:
                originaldfwithflags.loc[ix,'quality']=c.badqc

    dataframe.save(originaldfwithflags.fillna('None'),#
                   config['general']['outputfolder'] + stationid + '_original_sampling_flags.out')
except Exception as e:
    logger.error('Error processing station: ' + stationid)
    logger.error(sys.exc_info())
logger.info('Elapsed time... ' + str(time.time() - initime) + ' seconds')

