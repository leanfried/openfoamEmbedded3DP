#!/usr/bin/env pvpython
'''Collecting line traces through the bath in vtk files. Scripting for many folders and many images and tables.'''

# external packages
import os
import logging
import sys
from paraview.simple import * # import the simple module from the paraview

# local packages
from paraview_line import csvfolder, convertToRelative

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

    # load the virtual environment
virtualEnv = os.path.join(parentdir, 'env', 'Scripts', 'activate_this.py')
if sys.version_info.major < 3:
    execfile(virtualEnv, dict(__file__=virtualEnv))
else:
    exec(open(virtualEnv).read(), {'__file__': virtualEnv})
    
from config import cfg
import folderparser as fp

# logging
LOGGERDEFINED = fp.openLog(os.path.realpath(__file__), False, level="DEBUG")

# info
__author__ = "Leanne Friedrich"
__copyright__ = "This data is publicly available according to the NIST statements of copyright, fair use and licensing; see https://www.nist.gov/director/copyright-fair-use-and-licensing-statements-srd-data-and-software"
__credits__ = ["Leanne Friedrich"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Leanne Friedrich"
__email__ = "Leanne.Friedrich@nist.gov"
__status__ = "Production"


#################################################################

#------------------------------

tlist = [2.5]        # times at which to collect the traces
# xlist = [-0.001]      # positions at which to collect the trace
xlist = [-0.001]
# zlist = [0.0005]
zlist = []

forceOverwrite = False # True to overwrite existing files

folders = []
# nlist = range(0,1000)  # list of nb folder numbers that we will search
nlist = [200, 201, 202, 219, 137, 138, 139, 140, 141, 142, 143]

SERVERFOLDER = cfg.path.server
# topfolders = [os.path.join(SERVERFOLDER, 'yieldingsweep', 'HBHByielded', s) for s in ['k', 'n', 'tau0']]
# topfolders = topfolders + [os.path.join(SERVERFOLDER, 'yieldingsweep', 'LapRD')]
topfolders = [os.path.join(cfg.path.server, 'conicalnozzle', s) for s in ['orig', 'speed_sweep', 'diameter', 'newtonian', 'k']]
for topfolder in topfolders:
    for f in os.listdir(topfolder):
        if f.startswith('cn'):
            if f.endswith('hor'):
                try:
                    n1 = float(f[2:-3])
                except:
                    n1 = f[2:-3]
            else:
                try:
                    n1 = float(f[2:])
                except:
                    n1 = f[2:]
            if n1 in nlist:
                folders.append(os.path.join(topfolder, f))
                
logging.info(f'Exporting line traces.\n\
            X positions: {[convertToRelative(x) for x in xlist]} mm behind nozzle.\n\
            Z positions: {[1000*(x) for x in zlist]} mm above nozzle bottom.\n\
            Time list: {tlist} s.\n\
            Folders:{[os.path.basename(f) for f in folders]}')
                

for folder in folders:
    logging.debug('Checking '+folder)
    for xpos in xlist:
        csvfolder(folder, 'x', xpos, tlist, forceOverwrite=forceOverwrite)
    for zpos in zlist:
        csvfolder(folder, 'z', zpos, tlist, forceOverwrite=forceOverwrite)
print('Done exporting csv files')
