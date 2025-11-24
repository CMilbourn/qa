#!/usr/bin/env python
# coding: utf-8
# Wrapper script to run QA analysis for multiple datasets

import os
import sys
from datetime import datetime

# Import the multisubj version which handles multiple files
sys.path.append('/Users/cmilbourn/Documents/GitHub/qa/')

if __name__ == "__main__":
    # Define all 16 dataset file paths with optional TR overrides
    # First 8 files: TR will be read from .json files
    # Last 8 files: TR specified manually from the table
    dataset_configs = [
        # Files 1-8: Sweet Data with JSON TR values
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_11_fmri_MB3_ARC2_fMRI_1.5_mm_iso.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_7_fmri_MB3_ARC2_fMRI_2mm_1.5.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_4_fmri_MB3_ARC2_fMRI_2mm.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit002/func/sub001-visit002-ses001-task-rest-bold-pre.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-9-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-8-fmri_MB3_ARC2_fMRI_3mm-20251009110105.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105.nii.gz' },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.nii.gz' },
        
        # Files 9-16: BGI Data with manual TR values from the table
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1_MB3_single_echo_15_1.nii.gz', 'TR': 1.0 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p5_MB2_doublecho_13_1_ws_map.nii.gz', 'TR': 1.5 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p5_MB3_doublecho_14_1_ws_map.nii.gz', 'TR': 1.5 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB2_doublecho_9_1_ws_map.nii.gz', 'TR': 1.25 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB2_S1p8_11_1_ws_map.nii.gz', 'TR': 1.25 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB3_doublecho_8_1_ws_map.nii.gz', 'TR': 1.25 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB3_S1p8_10_1_ws_map.nii.gz', 'TR': 1.25 },
        { 'path': '/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR2_MB3_doublecho_2_1_ws_map.nii.gz', 'TR': 2.0 },
    ]
    
    # Verify files exist and filter to only existing ones
    existing_configs = []
    print("Checking file paths...")
    for cfg in dataset_configs:
        fpath = cfg['path']
        if os.path.exists(fpath):
            existing_configs.append(cfg)
            tr_info = f" (TR={cfg['TR']}s)" if 'TR' in cfg else " (TR from JSON)"
            print(f"✓ Found: {os.path.basename(fpath)}{tr_info}")
        else:
            print(f"✗ Path does not exist: {fpath}")

    if not existing_configs:
        print("\nNo files found to process!")
        sys.exit(1)

    dataset_configs = existing_configs
    
    print(f"\nTotal files to process: {len(dataset_configs)}")
    print("\nTo run these files, execute:")
    print("python qa_run_nophase_V3_multisubj.py")
    print("\n(Update that script's dataset_configs with the list above)")
