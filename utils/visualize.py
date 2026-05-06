'''
visualize-util
Created on 19 may. 2018
@author: AMG
Debugged on 13/VI/2023
'''

import matplotlib.pyplot as plt

def plotsubplots(dfs, station,folder_vis):

    plt.figure(1,figsize=(12, 7.5))
    plt.suptitle('SELENE QC output. Station ' + station)
    for df in dfs:
        plt.subplot(df[3])
        plt.plot(df[0],label=df[1],marker=df[5],linestyle=df[6],linewidth=df[9],ms=df[4],color=df[2])
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.25),  shadow=True, ncol=2)
        plt.ylabel('Sea level (mm)')
        plt.margins(df[7], df[8])
    plt.subplots_adjust(hspace=0.4)
    plt.savefig(folder_vis+"SELENEQC_graphics_Station_" + station + ".png")
    #plt.show()
def plot(dfs, text):
    plt.figure(1,figsize=(14, 4))
    plt.suptitle('Plot: ' + text)
    for df in dfs:
        plt.plot(df[0],label=df[1],marker=df[4],linestyle=df[5],ms=df[3],color=df[2])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),  shadow=True, ncol=2)
    plt.ylabel('Sea level (mm)')
    plt.tight_layout(pad=3.0)
    plt.savefig(text+'.png')
    plt.show()
