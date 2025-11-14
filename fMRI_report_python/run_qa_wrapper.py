#!/usr/bin/env python
# coding: utf-8
# Wrapper script to run QA analysis with specific parameters

from qa_run_nophase_V3 import run_qa_single_path

if __name__ == "__main__":
    # Set your data location and file pattern here
    mypathname = '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/'
    pathname_m = mypathname + 'func/'
    extension = '.nii.gz'  # this can be .nii or .nii.gz
    
    # Search pattern for filenames
    filename_pattern = 'sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105'
    
    # Run the QA analysis
    run_qa_single_path(mypathname, pathname_m, extension, filename_pattern)
