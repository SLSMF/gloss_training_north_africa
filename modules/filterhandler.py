'''
filter-module
Created on 5 jun. 2018
Updated on 13/VI/2023
@author: AMG
'''
import modules.filterkaiser as filterkaiser
import modules.filterpugh as filterpugh
def filt(filtername,df_input,minsampling,logger,config,c):#Jue changed df to df_input, so we do not have confusion over df_input and df (output)
    if filtername == 'kaiser':
        return filterkaiser.filt(df_input,minsampling,logger,config)
    elif filtername == 'pugh':
        return filterpugh.filt(df_input,logger,c)#
    else:
        logger.error('Filter option ' + filtername + ' not available.')
