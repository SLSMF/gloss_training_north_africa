'''
selene
Created on 9 jun. 2018
Debugged on 17 apr. 2026
@author: AMG

python selenevis.py [option:e.g. -station] [target_station] 
'''
import os
base_dir=os.path.dirname(os.path.abspath(__file__))

import sys
import configparser
import utils.visualize as visualize
import utils.iofilehandler as iofilehandler
import json
import configuration.constants as c
import logging

folder_vis=os.path.join(base_dir,"outputs/")
logger = logging.getLogger('selenevis')
fh = logging.FileHandler(c.logfilevis)
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(fh)
logger.setLevel(logging.INFO)
config = configparser.ConfigParser()
config.read(c.configini)
option = sys.argv[1]
with open(c.stationsfile) as f:
    stations = json.load(f)
if option == "-station":
    station = sys.argv[2] 
    dfs = []
    try:
        df = iofilehandler.txtfile2dataframe(folder_vis + station + '_original_sampling_flags.out',
                                             None, [0, 1], "\"%Y-%m-%d%H:%M:%S\"", 2, 4,logger) 

        df=df[df.quality!=c.nullqc]
        dfs.append([df[df.quality != c.badqc][['data']],'Orig. sampling SLEV : OK', '#2980b9',311,1.2,'o','None', 0, 0.05, 0.5])
    except:
        df = iofilehandler.txtfile2dataframe(folder_vis + station + '_original_sampling_buddy.out',
                                             None, [0, 1], "\"%Y-%m-%d%H:%M:%S\"", 2, 4,logger)
        df=df[df.quality!=c.nullqc]
        dfs.append([df[df.quality != c.badqc][['data']],'Orig. sampling SLEV: OK (after buddy-checking) : OK', '#2980b9',311,1.2,'o','None', 0, 0.05, 0.5])
    try:

        df_b = iofilehandler.txtfile2dataframe(folder_vis+ station + '_original_sampling_buddy.out', None, [0, 1],
            "\"%Y-%m-%d%H:%M:%S\"", 2, 4, logger) 
        df_b=df_b[df_b.quality!=c.nullqc]
        dfs.append([df_b[df_b.quality == 2][['data']], None, 'blueviolet',
             311, 2.5, 'o', 'None', 0, 0.05, 0.5])
        dfs.append([df_b[df_b.quality == 3][['data']], None, 'darkorange',
             311, 2.5, 'o', 'None', 0, 0.05, 0.5])

        dfs.append([df_b[df_b.quality == c.badqc][['data']],None,'#ED0DD9',311,2.5,'o','None', 0, 0.05, 0.5])
    except:
        pass
    try:
        dfs.append([df[df.quality == c.badqc][['data']],'Orig. sampling SLEV : BAD','#e71111',311,2.5,'o','None', 0, 0.05, 0.5])
    except:
        pass
    try:
        df_bh = iofilehandler.txtfile2dataframe(folder_vis+station+'_hourly_slev_buddy.out', None, [0,1], "\"%Y-%m-%d%H:%M:%S\"", 2, 3, logger)
        dfs.append([df_bh[df_bh.quality != c.badqc][['data']],'Hourly SLEV: OK','#FA8072',312,3.5,'o','None', 0, 0.05, 0.5])
        dfs.append([df_bh[df_bh.quality == c.badqc][['data']], 'Hourly SLEV: BAD (after buddy-checking)', '#ED0DD9', 312, 3.5, 'o','None', 0, 0.05, 0.5])
    except:
        pass
    try:
        df_t = iofilehandler.txtfile2dataframe(folder_vis+station+'_hourly_tide_buddy.out', None, [0,1], "\"%Y-%m-%d%H:%M:%S\"", 2, 3, logger)#
        dfs.append([df_t[df_t.quality!=c.badqc][['data']],'Hourly tide',"#96771c",313,1.8,'o','None', 0, 2, 0.5])
    except:
        pass
    try:
        df_s = iofilehandler.txtfile2dataframe(folder_vis+station+'_hourly_surge_buddy.out', None, [0,1], "\"%Y-%m-%d%H:%M:%S\"", 2, 3, logger)#
        dfs.append([df_s[df_s.quality!=c.badqc][['data']],'Hourly surge','#1f3327',313,1.8,'o','None', 0, 2, 0.5])
    except:
        pass
    try:
        visualize.plotsubplots(dfs,stations[station]['name'],folder_vis)
    except:
        visualize.plotsubplots(dfs, station,folder_vis)
elif option == "-files":
    files = sys.argv[2].split(',')
    dfs = []
    for file in files:
        try:
            df = iofilehandler.txtfile2dataframe(file, None, [0,1], "\"%Y-%m-%d%H:%M:%S\"", 2, 3, logger)
            dfs.append([df[df.quality != c.badqc][['data']],file+':OK','#2274a5',1.5,'o','None'])
            dfs.append([df[df.quality == c.badqc][['data']],file+':BAD','#e71111',2.5,'o','None'])
        except IndexError:
            df = iofilehandler.txtfile2dataframe(file, None, [0,1], "\"%Y-%m-%d%H:%M:%S\"", 2, None, logger)
            dfs.append([df[['data']],file,'#2274a5',1.5,'o','None'])
    visualize.plot(dfs,sys.argv[2])
else:
    print("Unknown option. Please, use -station <stationid> or -files <file1,file2,file3>")

