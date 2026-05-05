'''
selenemath-util
Created on 19 may. 2018
updated/debugged on 15 apr. 2026
@author: AMG
'''
import numpy as np

def rmse(predictions, targets):
    return np.sqrt(((predictions - targets) ** 2).mean())
