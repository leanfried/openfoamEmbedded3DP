#!/usr/bin/env python
'''Plotting line traces from Paraview'''

# external packages
import sys
import os
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Union, Any, TextIO
import logging

# local packages
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from plot_general import *
import interfacemetrics as intm

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
for s in ['matplotlib', 'imageio', 'IPython', 'PIL']:
    logging.getLogger(s).setLevel(logging.WARNING)

# plotting
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['font.size'] = 10


#-------------------------------------------

def linePlot(folder:str, time:float, ax:plt.Axes, color, yvar:str='vx', label:str='', zname:str='z', zunits:str='mm', **kwargs) -> None:
    '''plot the result of a line trace collected with paraview
        folder is the simulation to plot
        time is the time at which to collect the line
        ax is the axis to plot on
        color is the color of the line
        yvar is 0 to plot velocities, 1 to plot viscosities
        label is the label to write on the line
        zname is the variable to plot on the x axis
        zunits = 'mm' or any other value in legendUnique, e.g. 'nozzle_inner_width'
        '''
    t1,units = intm.importLine(folder, time, **kwargs)
    if len(t1)==0:
        logging.warning(f'Line file is missing in {folder}')
        return 
    t1 = t1.sort_values(by=zname)
    if zname=='z':
        le = fp.legendUnique(folder)
        t1[zname] = [float(le['nozzle_bottom_coord'])-zi for zi in t1[zname]]
        # shift origin up
    
    if not zunits=='mm':
        le = fp.legendUnique(folder)
        t1[zname] = t1[zname]/float(le[zunits])

    
    if yvar in t1:
        ystrink = yvar
        ystrsup = yvar
    elif yvar=='nu':
        tp = extractTP(folder)
        ystrsup = 'nu_sup'
        ystrink = 'nu_ink'
        # viscosity yvar
        if 'nu_sup' in t1:
            t1['nu_sup']=t1['nu_sup']*10**3 # this is specifically when the density is 10**3 kg/m^3
        else:
            nu_suplist = [tp['nusup'] for i in range(len(t1))]
            t1['nu_sup'] = nu_suplist
        if 'nu_ink' in t1:
            t1['nu_ink']=t1['nu_ink']*10**3
        else:
            nu_inklist = [tp['nuink'] for i in range(len(t1))]
            t1['nu_ink'] = nu_inklist
    elif yvar=='shearrate':
        ystrsup = 'shearrate'
        ystrink = 'shearrate'
        t1['shearrate'] = [np.linalg.norm(np.array([[row['shearrate0'],row['shearrate1'],row['shearrate2']],[row['shearrate3'],row['shearrate4'],row['shearrate5']],[row['shearrate6'],row['shearrate7'],row['shearrate8']]])) for i,row in t1.iterrows()]
    else:
        raise NameError(f'yvar must be column in line csv or \'nu\', given {yvar}')

    inkPts = t1[t1['alpha']>0.5]

    
    minx = min(inkPts[zname])
    maxx = max(inkPts[zname])
    supPtsLeft = t1[t1[zname]<minx]
    supPtsRight = t1[t1[zname]>maxx]
    
    for suppts in [supPtsLeft, supPtsRight]:
        ax.plot(suppts[zname], suppts[ystrsup], color=color, linewidth=0.75)
        
    ax.plot(inkPts[zname], inkPts[ystrink], color=color, linestyle='--', linewidth=0.75)
    pts = t1[(t1[zname]==minx) | (t1[zname]==maxx)]
#     ax.scatter(pts[zname], pts[ystrink], color=color, label=label)
#     ax.scatter(pts[zname], pts[ystrsup], color=color)
    
    
def labDict(yvar:str) -> str:
    return varNicknames().labDict(yvar)
#     '''dictionary for variable headers in line traces'''
#     if yvar=='vx':
#         return ('$x$ velocity (mm/s)')
#     elif yvar=='vz':
#         return ('$z$ velocity (mm/s)')
#     elif yvar=='nu':
#         return ('Viscosity (Pa$\cdot$s)')
#     elif yvar=='p':
#         return ('Pressure (Pa)')
#     else:
#         return (yvar)


def linePlots(folders:List[str], cvar, time:float=2.5, imsize:float=3.25, yvar:str='vx', legend:bool=True, xlabel:bool=True, ylabel:bool=True, zunits:str='mm', **kwargs) -> plt.Figure:
    ''' plot line traces for multiple folders
    folders is a list of folders (e.g. nb16, nb17) to include in the plot
    cvar is the function to use for deciding plot colors. func should be as a function of transport properties dictionary or a string e.g. func could be multfunc or func could be 'nozzle_angle'
    time is the time at which to collect the line trace
    imsize is the total size of the figure
    yvar is the variable to plot on the y axis, e.g. 'nu' or 'shearrate'
    legend=True to put a legend on the plot
    xlabel=True to put a label on the x axis
    ylabel=True to put a label on the y axis
    zunits = 'mm' or any value in legendUnique, e.g. 'nozzle_inner_width'
    '''
    
    
    if 'ax' in kwargs and 'fig' in kwargs:
        ax = kwargs['ax']
        fig = kwargs['fig']
        kwargs.pop('ax')
    else:
        fig, ax = plt.subplots(nrows=1, ncols=1, sharex=False, figsize=(imsize, imsize))
    
    if type(cvar) is str: 
        # this is a column header from extractTP
        tplist = pd.DataFrame([extractTP(folder) for folder in folders])
        tplist.sort_values(by=cvar, inplace=True)
        tplist.reset_index(drop=True, inplace=True)
        tplist[cvar] = expFormatList(list(tplist[cvar]))
        cm = sns.color_palette('viridis', as_cmap=True) # uses viridis color scheme
        for i,row in tplist.iterrows():
            linePlot(row['folder'], time, ax, cm(i/len(tplist)), yvar, cmap=cm, label=row[cvar], zunits=zunits, **kwargs)
    else:
        # this is a function operated on extractTP
        funcvals = unqListFolders(folders, cvar)
        cmap = sns.diverging_palette(220, 20, as_cmap=True)
        for f in folders:
            val = folderToFunc(folder, colorf)
            fracval = decideRatio(val, rang)
            if fracval==0.5:
                color = 'gray'
            else:
                color = cmap(fracval)
            linePlot(f, time, ax, color, yvar, label=decideFormat(val), **kwargs)
    if legend:
        ax.legend(bbox_to_anchor=(1, 1), loc='upper right', ncol=1)
    if xlabel:
        zunits = varNickname(zunits, short=True)
        ax.set_xlabel(f'$z$ ({zunits})')
    if ylabel:
        ax.set_ylabel(labDict(yvar))
    if yvar=='nu' or yvar=='shearrate':
        ax.set_yscale('log')
    return fig

def linePlots0(topFolder:str, exportFolder:str, cvar:str, time:float, imsize:float=6.5, yvar:str='vx', overwrite:bool=False, export:bool=True, fontsize:int=8, **kwargs) -> plt.Figure:
    '''plot the value over the line trace
    topFolder holds all of the simulations
    exportFolder is the folder to export data to
    cvar is the function to use for deciding plot colors. func should be as a function of transport properties dictionary or a string e.g. func could be multfunc or func could be 'nozzle_angle'
    time is the time at which to collect the line trace
    imsize is the total size of the figure
    yvar is the variable to plot on the y axis, e.g. 'nu' or 'shearrate'
    overwrite=True to overwrite existing files
    export=True to export values
    '''

    
    labels = ['line', time, yvar, cvar]
    fn = intm.imFn(exportFolder, labels, topFolder, **kwargs) # output file name
    if not overwrite and os.path.exists(fn+'.png'):
        return

    plt.rc('font', size=fontsize) 
    
    folders = fp.caseFolders(topFolder)
    folders, _ = listTPvalues(folders, **kwargs) # remove any values that don't match
    
    if len(folders)==0:
        return

    if type(yvar) is list:
        # get bottom of nozzle
        le = fp.legendUnique(folders[0])
        nb = float(le['nozzle_bottom_coord'])
        
        # create plots
        fig, axs = multiPlots(len(yvar), sharex=True, imsize=imsize)
        cols = len(axs[0])
        rows = len(axs)
        axlist = axs.flatten()
        
        # iterate through y variables
        for i,m in enumerate(yvar):
            xlabel = ((i/cols+1)>=np.floor(len(yvar)/cols))
            legend = (i==(len(yvar)-1))
            # plot line
            linePlots(folders, cvar, time=time, yvar=m, ax=axlist[i], fig=fig, legend=legend, xlabel=xlabel, **kwargs)
        for ax in axlist:
#             ax.vlines([0], 0, 1, transform=ax.get_xaxis_transform(),  color='#888888', linestyle='--', linewidth=0.75)
            setSquare(ax)
        subFigureLabels(axs)
        plt.subplots_adjust(hspace=0)
        fig.tight_layout()
    else:
        fig = linePlots(folders, cvar, time, imsize, yvar, **kwargs)
    if export:
        intm.exportIm(fn, fig) # export figure



#------------------------------


def linePressure(folder:str) -> dict:
    '''get the pressure differential across the nozzle'''
    file = os.path.join(folder, 'line_t_10_z_0.5.csv')
    if not os.path.exists(file):
        return {}, {}
    data, units = intm.importPointsFile(file) 
    pUpstream = data[(data.x>-2.9)&(data.x<-2.87)].p.max() # upstream pressure
    pDownstream = data[(data.x>-1.96)&(data.x<-1.9)].p.max() # downstream pressure
    dp = pUpstream-pDownstream
    pdict = {'pU':pUpstream, 'pD':pDownstream, 'dP':dp}
    units = {'pU':units['p'], 'pD':units['p'], 'dP':units['p']}
    meta, u = extractTP(folder, units=True)
    retval = {**meta, **pdict}
    units = {**u, **units}
    return retval, units

def linePressureRecursive(folder:str) -> dict:
    '''find line pressures for all sims in folder, all the way down'''
    if not os.path.isdir(folder):
        return [], {}
    r,u = linePressure(folder)
    if len(r)>0:
        return [r],u
    else:
        rlist = []
        units = {}
        for f in os.listdir(folder):
            r,u = linePressureRecursive(os.path.join(folder, f))
            if len(r)>0:
                rlist = rlist+r
                units = u
        return rlist, units

def linePressures(topfolder:str, exportFolder:str, filename:str) -> dict:
    '''find pressure differential between upstream and downstream surface of nozzle along the line traces for all sims in folder and export'''
    rlist, units = linePressureRecursive(topfolder)
    tt = pd.DataFrame(rlist)
    if os.path.exists(exportFolder):
        fn = os.path.join(exportFolder, filename)
        col = pd.MultiIndex.from_tuples([(k,v) for k, v in units.items()])
        data = np.array(tt)
        df = pd.DataFrame(data, columns=col)       
        df.to_csv(fn)
        logging.info(f'Exported {fn}')
    return tt,units

    
    