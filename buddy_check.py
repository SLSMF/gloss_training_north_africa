#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: JLY
Debugged on 17 apr. 2026
python buddy_check.py [target_station] [target_year]

"""
import os
base_dir=os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
import json
import configparser
import pandas as pd
import logging
import math
import numpy as np
import utils.utide_construct as utide_construct
import configuration.constants as c
import utils.dataframe as dataframe
import os
from scipy import signal,stats
import sys
from dateutil.relativedelta import relativedelta
import monthly_ave
logger = logging.getLogger('selene')


def median_without_outliers(data,tol_groupby):
    data = np.array(data)
    d = np.abs(data - np.median(data))
    return np.median(data[d<tol_groupby])

def load_files(target_station,config):

    originaldf = pd.read_csv(os.path.join("outputs", str(target_station) + '_original_sampling_flags.out'), sep=" ",
                             header=None, dtype="str")
    originaldf.columns = ["date_aux", "data", "quality_old", "quality"]
    originaldf["date"] = pd.to_datetime(originaldf.date_aux, format="%Y-%m-%d %H:%M:%S", infer_datetime_format=False)

    originaldf = originaldf[["data", "quality_old", "quality", "date"]].set_index("date")
    originaldf = originaldf.replace("None", np.nan)
    originaldf = originaldf.astype({"data": "float64", "quality_old": "float64", "quality": "float64"})

    hourlydf = originaldf.loc[originaldf.quality==1,["data","quality"]].resample("1H").first()
    try:
        hourlysurge_aux = utide_construct.tide_reconstruct(hourlydf, target_station, constit_out=None)
        hourlysurge = {}
        hourlysurge["data"] = pd.to_numeric(hourlysurge_aux["RES_noAstroTide"], errors='coerce').astype("float64")
        hourlysurge["quality"] = 1
        hourlysurge = pd.DataFrame(hourlysurge, index=hourlysurge_aux.index)
        have_surge = "yes"
    except:
        have_surge = "no"
        hourlysurge=pd.DataFrame(columns=["data","date"])
    df_avg=np.nanmedian(hourlydf.data)
    q_df = np.nanpercentile(np.abs(hourlydf.data[np.log10(np.abs(hourlydf.data)) < 6] - df_avg), q=75)

    monthlydf, dailydf= monthly_ave.monthly_ave(hourlydf[hourlydf.quality == 1],target_station)
    monthlydf["quality"]=1
    mean_oneselfM=np.nanmean(monthlydf.data)
    try:
        alt_monthly=pd.read_csv(os.path.join("altimeter_data",str(target_station)+'_alt_monthly.csv'),sep=";")
        alt_monthly["date"]=pd.to_datetime(alt_monthly.date,format="%Y%m",infer_datetime_format=False)
        alt_monthly=alt_monthly[["data","date"]].set_index("date")
        alt_monthly=alt_monthly.astype({"data":"float64"})
        mean_altM=np.nanmean(alt_monthly.data)
        alt_monthly["data"]=alt_monthly.apply(lambda x: (x["data"]-mean_altM)*1000+mean_oneselfM,axis=1)
    except:
        alt_monthly = pd.DataFrame(columns=["data", "date"])
    return originaldf,hourlydf,hourlysurge,have_surge,q_df,alt_monthly,monthlydf,dailydf,mean_oneselfM

def compare_hourly_monthly(target_station,stations,code_guide,have_surge,hourlysurge,monthlydf,mean_oneselfM,config):
    buddy_dict={};buddy_dictM={}
    num_buddies = 0;iter1 = 0
    bud_check_diff={}
    while (iter1 < 2):
        for stationid in stations:
            longitude_target = stations[target_station]["longitude"]
            latitude_target = stations[target_station]["latitude"]
            longitude1 = stations[stationid]["longitude"]
            latitude1 = stations[stationid]["latitude"]
            if (math.sqrt((longitude1 - longitude_target) ** 2 + (latitude1 - latitude_target) ** 2) > max(0,
                    0.1 + 0.2 * (iter1 - 1))) and \
                    (math.sqrt((longitude1 - longitude_target) ** 2 + (latitude1 - latitude_target) ** 2) < (
                            0.1 + 0.2 * iter1)):  
                if (str(code_guide.loc[
                            code_guide.code2.astype("str") == str(stationid), "stationGeneralId"]) != str(
                        code_guide.loc[code_guide.code2.astype("str") == str(target_station), "stationGeneralId"])) \
                        and ((code_guide.loc[code_guide.code2.astype("str") == str(
                    stationid), "sampling"].values == "one_sampling") | (code_guide.loc[
                                                                             code_guide.code2.astype("str") == str(
                                                                                 stationid), "sampling"].values == "max_int")) \
                        and num_buddies < 2:  

                    try:
                        buddyH_aux = pd.read_csv(os.path.join("outputs", str(stationid) + '_hourly_slev.out'),
                                                 sep=" ", header=None, dtype="str")
                        buddyH_aux.columns = ["date_aux", "data", "quality"]
                        buddyH_aux["date"] = pd.to_datetime(buddyH_aux.date_aux, format="%Y-%m-%d %H:%M:%S",
                                                            infer_datetime_format=False)
                        buddyH_aux = buddyH_aux[["data", "quality", "date"]].set_index("date")
                        buddyH_aux=buddyH_aux.replace("None",np.nan)
                        buddyH_aux = buddyH_aux.astype({"data": "float64", "quality": "int"})
                        if have_surge=="yes":
                            try:
                                buddyH_aux2 = utide_construct.tide_reconstruct(buddyH_aux,stationid,constit_out=None)
                                buddyH = {}
                                buddyH["data"] = pd.to_numeric(buddyH_aux2["RES_noAstroTide"], errors='coerce').astype("float64")
                                buddyH["quality"] = 1
                                buddyH = pd.DataFrame(buddyH, index=buddyH_aux2.index)
                                if len(buddyH_aux.data)>500:
                                    bud_check1 = pd.merge(hourlysurge.data[~np.isnan(hourlysurge.data)], buddyH.data[~np.isnan(buddyH.data)], left_index=True,
                                                     right_index=True,
                                                     how="inner", suffixes=('_oneself', '_buddy'))
                                    for ii_bud1 in range(len(bud_check1)):
                                        if abs(bud_check1.data_oneself[ii_bud1])<abs(bud_check1.data_buddy[ii_bud1]) and \
                                                abs(bud_check1.data_buddy[ii_bud1]-bud_check1.data_oneself[ii_bud1])>1000:
                                            buddyH.loc[buddyH.index==bud_check1.index[ii_bud1],"quality"]=c.badqc
                                    buddy_dict[stationid]=buddyH.loc[buddyH.quality!=c.badqc]
                            except:
                                pass
                        buddyM, buddyD= monthly_ave.monthly_ave(buddyH_aux.loc[buddyH_aux.quality == 1],stationid)
                        buddyM["quality"]=1
                        mean_buddyM=np.nanmean(buddyM.data)
                        buddyM["data"] = buddyM.apply(lambda x: x["data"] - mean_buddyM + mean_oneselfM,axis=1)
                        bud_check2 = pd.merge(monthlydf.data[~np.isnan(monthlydf.data)], buddyM.data[~np.isnan(buddyM.data)], left_index=True,
                                             right_index=True,
                                             how="inner", suffixes=('_oneself', '_buddy'))
                        for ii_bud2 in range(len(bud_check2)):
                           if abs(bud_check2.data_oneself[ii_bud2]-mean_oneselfM)<abs(bud_check2.data_buddy[ii_bud2]-mean_oneselfM) \
                                   and abs(bud_check2.data_buddy[ii_bud2]-bud_check2.data_oneself[ii_bud2])>500:
                                buddyM.loc[buddyM.index==bud_check2.index[ii_bud2],"quality"]=c.badqc
                        buddy_dictM[stationid] = buddyM.loc[buddyM.quality != c.badqc]
                        bud_check_diff[stationid] = bud_check2.diff(periods=1,axis=1)
                        num_buddies += 1
                    except:
                        pass
        iter1+=1
    return buddy_dict, buddy_dictM, bud_check_diff,num_buddies


def att_data(hourlydf, q_df, mean_oneselfM, badixs):
    attcount = 1;
    attlimit = 25
    roll_mean_df = hourlydf.data.rolling('12h').mean() 
    roll_std_df = hourlydf.data.rolling('12h').std()
    std_df = np.nanstd(hourlydf.data)
    if math.log10(q_df) < 3:
        const_att = 50 ** (3 - math.log10(q_df))
    else:
        const_att = 1
    frac1 = const_att * 2;
    frac2 = const_att * 3
    for ix in range(len(hourlydf.index.values)):
        if abs(roll_mean_df[ix] - mean_oneselfM) < 1000:
            const_att2 = 10
        else:
            const_att2 = 1
        if abs(hourlydf.data[ix] - roll_mean_df[ix]) < (q_df / (const_att2 * frac1)) and roll_std_df[ix] < (
                std_df / (const_att2 * frac2)):
            attcount += 1
            if attcount == attlimit:
                badixs.append(hourlydf.index.values[(ix - attlimit + 1):(ix + 1)])
            elif attcount > attlimit:
                badixs.append(hourlydf.index.values[ix])
        else:
            attcount = 1
    return badixs


def drift(hourlydf, bud_check_diff, badixs):
    driftcount = 1;
    driftlimit = 3
    badixs_aux3 = []
    for stationid in bud_check_diff.keys():
        for ix in range(len(bud_check_diff[stationid].index.values)):
            if abs(bud_check_diff[stationid].data_buddy[ix] - bud_check_diff[stationid].data_oneself[ix]) > 100:
                driftcount += 1
                if driftcount == driftlimit:
                    badixs_aux3.append(bud_check_diff[stationid].index.values[(ix - driftlimit + 1):(ix + 1)])
                elif driftcount > driftlimit:
                    badixs_aux3.append(bud_check_diff[stationid].index.values[ix])
            else:
                driftcount = 1

    for ii_drift in badixs_aux3:
        try:
            for ii_drift2 in ii_drift:
                badixs.append(hourlydf.index[(hourlydf.index >= ii_drift2) \
                                             & (hourlydf.index <= (
                        pd.to_datetime(ii_drift2) + relativedelta(months=1)))])
        except:
            badixs.append(hourlydf.index[(hourlydf.index >= ii_drift) \
                                         & (hourlydf.index <= (
                    pd.to_datetime(ii_drift) + relativedelta(months=1)))])
    return badixs


def plot_buddy(target_station, neighbordict, neighbor2, self1, alt_monthly, num_buddies,have_surge,choice1):
    checking2=[]
    for key in list(neighbordict.keys()):
        neighbor2 = pd.concat([neighbor2, neighbordict[key]])
    neighbor2 = neighbor2.sort_index(ascending=True)
    neighbor2 = neighbor2[neighbor2.quality == 1]
    if num_buddies > 1:
        neighbor1 = neighbor2.resample(groupby_unit).apply(lambda x: median_without_outliers(x, tol_groupby))
    else:
        neighbor1 = neighbor2.copy(deep=True)

    neighbor1 = neighbor1.astype({"data": "float64", "quality": "float64"})  
    checking1 = pd.merge(self1.data[~np.isnan(self1.data)], neighbor1.data[~np.isnan(neighbor1.data)], left_index=True,
                         right_index=True,
                         how="inner", suffixes=('_oneself', '_buddy'))
    if choice1 == "monthly":
        checking2 = pd.merge(self1.data[~np.isnan(self1.data)],
                             alt_monthly.data[~np.isnan(alt_monthly.data)],
                             left_index=True, right_index=True, how="inner", suffixes=("_oneself",
                                                                                       "_alti")) 
    return checking1,checking2



def buddy_check(target_station,target_year):
    code_guide_path=os.path.join(base_dir,"code_guide.csv")
    code_guide=pd.read_csv(code_guide_path,header=0,sep=";")
    code_guide["stationGeneralId"]=code_guide.apply(lambda x: str(x["code2"])[1:-2],axis=1)
    with open(c.stationsfile) as f:
        stations = json.load(f)
    config = configparser.ConfigParser()
    config.read(c.configini)
    originaldf,hourlydf,hourlysurge,have_surge,q_df,alt_monthly,monthlydf,dailydf,mean_oneselfM=load_files(target_station,config)

    buddy_dict, buddy_dictM, bud_check_diff,num_buddies= \
        compare_hourly_monthly(target_station,stations,code_guide,have_surge,hourlysurge,monthlydf,mean_oneselfM,config)
    badixs = []
    try:
        thislist = ["hourly", "monthly"]
        for choice1 in thislist:
            neighbor2 = pd.DataFrame([], columns=monthlydf.columns)
            if (choice1 == "hourly") and (have_surge=="yes"):
                neighbordict=buddy_dict
                groupby_unit="H"
                self1=hourlysurge.copy(deep=True)
                tol_groupby=1000
            elif choice1 == "monthly":
                neighbordict=buddy_dictM
                groupby_unit="MS"
                self1=monthlydf.copy(deep=True)
                tol_groupby=400
            if (choice1=="monthly")|((choice1=="hourly")and(have_surge=="yes")):
                checking1,checking2=plot_buddy(target_station, neighbordict, neighbor2, self1, alt_monthly, num_buddies,have_surge,choice1)
                badixs.append(checking1.index[(~np.isnan(checking1.data_buddy) & (np.abs(checking1.data_oneself-checking1.data_buddy) > 1000))])  
                if choice1 == "monthly":
                    badixs_aux3 = checking1.index[(~np.isnan(checking1.data_buddy) & (np.abs(checking1.data_buddy - checking1.data_oneself) > np.max([500])))] 
                    badixs_aux4=checking2.index[(~np.isnan(checking2.data_alti) & (np.abs(checking2.data_alti - checking2.data_oneself)>np.max([500])))]
                    badixs_aux2=np.append(badixs_aux3,badixs_aux4)
                    for ii_bad_monthly in range(badixs_aux2.size):
                        badixs.append(hourlydf.index[(hourlydf.index >= badixs_aux2[ii_bad_monthly]) \
                                                     & (hourlydf.index <= (
                                badixs_aux2[ii_bad_monthly] + relativedelta(months=1)))])

                    badixs=drift(hourlydf,bud_check_diff,badixs)

        badixs=att_data(hourlydf,q_df,mean_oneselfM,badixs)

        for badixs_aux in badixs:
            try:
               for badix in badixs_aux:
                    originaldf.loc[((originaldf.index >= badix) & (originaldf.index <= (pd.to_datetime(badix)+relativedelta(hours=1)))),"quality"]=c.badqc
            except:
                originaldf.loc[((originaldf.index >= badixs_aux) & (
                            originaldf.index <= (pd.to_datetime(badixs_aux) + relativedelta(hours=1)))), "quality"]=c.badqc
    except:
        pass
    originaldf = originaldf.loc[np.abs(originaldf.data)>=0, ["data","quality_old" ,"quality"]]
    originaldf=originaldf.astype({"quality":"int"})
    dataframe.save(originaldf.fillna("None"),config['general']['outputfolder']+str(target_station)+'_original_sampling_buddy.out')
    hourlyfiltered = originaldf[originaldf.quality==1].resample("H").mean()
    dataframe.save(hourlyfiltered.fillna("None"),config['general']['outputfolder']+str(target_station)+'_hourly_slev_buddy.out')
    try:
        tidesurge=utide_construct.tide_reconstruct(hourlyfiltered,target_station)
        dataframe.save(tidesurge['RES_noAstroTide'],config['general']['outputfolder']+str(target_station)+'_hourly_surge_buddy.out')
        dataframe.save(tidesurge['TIDE'],config['general']['outputfolder']+str(target_station)+'_hourly_tide_buddy.out')    
    except:
        pass
########################################################################################################################
#run function
buddy_check(str(sys.argv[1]),str(sys.argv[2]))
