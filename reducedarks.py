#!/usr/bin/env python

"""
Created on Wed Jul  8 02:12:39 2015

@author: keatonb
"""

# Imports.
# Standard libraries.
from __future__ import absolute_import, division, print_function
import os
import sys
import dateutil.parser
import numpy as np
# Installed packages.
from astropy.io import fits
from bs4 import BeautifulSoup
# Local modules.
import read_spe

def main(fpath_spe): 
    #Read in SPE data
    fpath_spe  = os.path.abspath(fpath_spe)
    spe = read_spe.File(fpath_spe)
    
    
    #How many frames?
    num_frames=spe.get_num_frames()
    #get all frames in SPE file
    #stack as 3D numpy array
    (frames,_)=spe.get_frame(0)
    frames=np.array([frames])
    for i in range(1,num_frames):
        (thisframe,_)=spe.get_frame(i)
        frames=np.concatenate((frames,[thisframe]),0)
    
    #median combine the frames
    master=np.median(frames,axis=0)
    

    #Write master dark to fits file
    
    #compile header information
    prihdr = fits.Header()
    prihdr['OBJECT'] = 'dark'
    prihdr['IMAGETYP'] = 'dark'
    
    if hasattr(spe, 'footer_metadata'):
        footer_metadata = BeautifulSoup(spe.footer_metadata, "xml")
        ts_begin = footer_metadata.find(name='TimeStamp', event='ExposureStarted').attrs['absoluteTime']
        dt_begin = dateutil.parser.parse(ts_begin)
        prihdr['TICKRATE'] = int(footer_metadata.find(name='TimeStamp', event='ExposureStarted').attrs['resolution'])
        prihdr['DATE-OBS'] = str(dt_begin.isoformat())
        prihdr['XBINNING'] = footer_metadata.find(name="SensorMapping").attrs['xBinning']
        prihdr['YBINNING'] = footer_metadata.find(name="SensorMapping").attrs['yBinning']
        prihdr['INSTRUME'] = footer_metadata.find(name="Camera").attrs['model']
        prihdr['TRIGGER'] = footer_metadata.find(name='TriggerResponse').text
        prihdr['COMMENT'] = "SPE file has footer metadata"
        prihdr['EXPTIME'] = str(float(footer_metadata.find(name='ExposureTime').text)/1000.)
        #prihdr['SOFTWARE'] = footer_metadata.find(name='Origin')
        prihdr['SHUTTER'] = footer_metadata.find(name='Mode').text
        if footer_metadata.find(name='Mode').text != 'AlwaysClosed':
            prihdr['WARNING'] = 'Shutter not closed for dark frame.'
            print("WARNING: Shutter not closed for dark frame.")
    else:
        prihdr['WARNING'] = "No XML footer metadata."
        print("WARNING: No XML footer metadata.")
        
        
    #put it all together
    hdu = fits.PrimaryHDU(master,header=prihdr)
    
    #write it out
    fitsfilename = fpath_spe.split('.spe')[0]+'_master.fits'
    hdu.writeto(fitsfilename,clobber=True)

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print('ERROR: must provide filename of SPE file.')
    else:
        main(sys.argv[1])
