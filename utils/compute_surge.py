'''
@author: JLY
last debugged on 13/VI/2023
'''

import utils.utide_construct as utide_construct
import pandas as pd
import numpy as np

def compute_tidesurge(df,stationid):
    tidesurge_aux= utide_construct.tide_reconstruct(df,stationid,constit_out=None)
    tidesurgedf={}
    tidesurgedf["RES_noAstroTide"]=pd.to_numeric(tidesurge_aux["RES_noAstroTide"],errors='coerce').astype("float64")
    tidesurgedf["TIDE"] = pd.to_numeric(tidesurge_aux["TIDE"], errors='coerce').astype("float64")
    tidesurgedf["quality"]=1
    tidesurgedf=pd.DataFrame(tidesurgedf,index=tidesurge_aux.index)
    tidesurgedf = tidesurgedf.loc[np.abs(tidesurgedf.TIDE)>=0, ["RES_noAstroTide","TIDE", "quality"]]
    tidesurgedf=tidesurgedf.astype({"quality":"int"})
    return tidesurgedf
