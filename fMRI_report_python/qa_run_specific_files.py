#!/usr/bin/env python
# Modified script to run QA for specific files only

import sys
sys.path.insert(0, '/Users/cmilbourn/Documents/GitHub/qa/')

# Import and execute the main script
import importlib.util
spec = importlib.util.spec_from_file_location("qa_script", "/Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python/qa_run_nophase_V12_MASK_40dyn_V6.py")
qa_module = importlib.util.module_from_spec(spec)

# Monkey-patch the main block before executing
original_code = spec.loader.get_code(spec.name)

# Execute the module but intercept the main block
import os
import subprocess
import numpy as np
import nibabel as nib
from glob import glob
import csv
from datetime import datetime

# Import required modules from the original script's imports
sys.path.append('/Users/cmilbourn/Documents/GitHub/qa/')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import Normalize
import nibabel as nib
from glob import glob
import json
import csv
from datetime import datetime
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN
    from PIL import Image
    PPTX_AVAILABLE = True
except ImportError:
    print('python-pptx not installed, PowerPoint generation will be skipped.')
    PPTX_AVAILABLE = False

from fMRI_report_python.functions import snr
from scipy.signal import detrend
from mpl_toolkits.mplot3d import Axes3D

# Now execute the original script to get all functions defined
exec(open('/Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python/qa_run_nophase_V12_MASK_40dyn_V6.py').read().split('if __name__ == "__main__":')[0])

# NOW run the main block with modified dataset_configs
if __name__ == "__main__":
    # Specific files to process
    dataset_configs = [
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/nifti/sub001/sub001_Phase2_2samples/func/sub001-visit004-ses001_task-2S_bold.nii.gz', 'TR': None },
        { 'path': '/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub010/sub010-visit002/func/sub010-visit002-ses001_task-2S_bold.nii.gz', 'TR': None }
    ]
    
    # Verify files exist
    existing_configs = []
    for cfg in dataset_configs:
        fpath = cfg['path']
        if os.path.exists(fpath):
            existing_configs.append(cfg)
            print(f"Found: {os.path.basename(fpath)}")
        else:
            print(f"Path does not exist: {fpath}")

    if not existing_configs:
        print("No files found to process!")
        exit(1)

    # Use verified list
    dataset_configs = existing_configs
    
    print(f"\nTotal files to process: {len(dataset_configs)}")
    
    # Create base output directory
    base_output_dir = '/Users/cmilbourn/Documents/tSNR_check_40dyn/qa_output_specific_files'
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Create a timestamped session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(base_output_dir, f'qa_session_{timestamp}')
    os.makedirs(session_dir, exist_ok=True)
    
    # List to store all metrics and output directories
    all_metrics = []
    all_output_dirs = []
    
    # Tracking arrays for per-file mask handling
    created_masks = []
    generated_masks = []
    missing_mask_failures = []
    
    # Per-file processing log for end-of-run summary
    processing_log = []
    
    # Process each file
    for file_idx, cfg in enumerate(dataset_configs):
        mag_file_path = cfg['path']
        tr_override = cfg.get('TR')
        
        print(f"\n{'='*80}")
        print(f"Processing file {file_idx + 1}/{len(dataset_configs)}: {os.path.basename(mag_file_path)}")
        print(f"{'='*80}")
        
        # Extract a clean name for this dataset
        core_filename = os.path.splitext(os.path.splitext(os.path.basename(mag_file_path))[0])[0]
        pathname_m = os.path.dirname(mag_file_path)

        print(f"Core filename: {core_filename}")

        # Create an output directory for saving plots
        output_directory = os.path.join(session_dir, f'{core_filename}')
        os.makedirs(output_directory, exist_ok=True)
        OUTPUT_DIR = os.path.abspath(output_directory)

        print(f"Output directory: {OUTPUT_DIR}")
        
        # Remove first 2 dummy volumes using fslroi
        extension = '.nii.gz'
        mag_file_nodummies = os.path.join(OUTPUT_DIR, core_filename + '_nodummies' + extension)
        print(f"Removing first 2 dummy volumes with fslroi...")
        fslroi_cmd = f"fslroi {mag_file_path} {mag_file_nodummies} 2 -1"
        result = subprocess.run(fslroi_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: fslroi failed: {result.stderr}")
            print("Proceeding with original file...")
            mag_file_to_use = mag_file_path
        else:
            print(f"Dummy volumes removed. Using: {mag_file_nodummies}")
            mag_file_to_use = mag_file_nodummies
        
        try:
            # Load magnitude data only
            print('Loading magnitude data...')
            nifti_img = nib.load(mag_file_path)
            imgm_cla, imgm_cla_affine = load_data(mag_file_to_use)
            print(f"Loaded data shape: {imgm_cla.shape}")
            
            # Check if 3D or 4D
            if imgm_cla.ndim < 4 or imgm_cla.shape[-1] < 3:
                print(f"Data is 3D or has too few timepoints (shape: {imgm_cla.shape}), using minimal processing...")
                metrics = process_data_single_volume(imgm_cla[:, :, :, 0] if imgm_cla.ndim == 4 else imgm_cla, 
                                                      imgm_cla_affine, core_filename, OUTPUT_DIR, 
                                                      mask_data=None, nifti_path=mag_file_path, nifti_img=nifti_img)
            else:
                # MASK (prefer per-file mask matching this magnitude)
                mag_base = os.path.splitext(os.path.splitext(os.path.basename(mag_file_to_use))[0])[0]
                mask_path = find_mask_file(pathname_m, mag_basename=mag_base)
                mask_data = None
                mask_path_used = None
                
                if mask_path:
                    try:
                        print(f"Found mask: {mask_path}")
                        mask_data, mask_affine = load_data(mask_path)
                        mask_path_used = mask_path
                        created_masks.append(mask_path)
                    except Exception as e:
                        print(f"Error loading mask: {e}")
                        mask_data = None
                else:
                    print("No mask file found.")
                    mask_data = None
                
                # Process and plot data
                metrics = process_data_nophase(imgm_cla, imgm_cla_affine, core_filename, OUTPUT_DIR, 
                                               mask_data, TR=tr_override, nifti_path=mag_file_path, nifti_img=nifti_img)
            
            all_metrics.append(metrics)
            all_output_dirs.append(OUTPUT_DIR)
            
            # Record successful processing
            processing_log.append({
                'input': mag_file_path,
                'status': 'completed',
                'output_dir': OUTPUT_DIR,
                'mask_used': bool(mask_data is not None),
                'mask_path': mask_path_used,
                'TR': metrics.get('TR')
            })
            
        except Exception as e:
            print(f"ERROR processing {mag_file_path}: {e}")
            import traceback
            traceback.print_exc()
            # Record failure in log
            processing_log.append({
                'input': mag_file_path,
                'status': 'failed',
                'error': str(e)
            })
            continue
    
    # Create combined PowerPoint presentation
    print(f"\n{'='*80}")
    print("Creating combined PowerPoint presentation...")
    print(f"{'='*80}")
    create_combined_powerpoint(session_dir, all_output_dirs, all_metrics)
    
    # Save combined metrics to CSV
    if all_metrics:
        csv_path = os.path.join(session_dir, f'qa_metrics_combined_{timestamp}.csv')
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = all_metrics[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for metrics in all_metrics:
                writer.writerow(metrics)
        print(f"\nCombined metrics CSV saved to: {csv_path}")

    # Summary of mask handling
    print("\nMask processing summary:")
    print(f"  Existing masks used: {len(created_masks)}")
    print(f"  Masks generated via BET: {len(generated_masks)}")
    if missing_mask_failures:
        print(f"  Datasets with mask creation failures: {len(missing_mask_failures)}")
        for fail in missing_mask_failures:
            print(f"    - {fail}")
    else:
        print("  No mask creation failures.")
    
    # Per-file processing summary list
    print("\nProcessing results by input file:")
    completed_count = sum(1 for r in processing_log if r.get('status') == 'completed')
    failed_count = sum(1 for r in processing_log if r.get('status') == 'failed')
    total_requested = len(dataset_configs)
    print(f"  Requested: {total_requested}")
    print(f"  Completed: {completed_count}")
    print(f"  Failed: {failed_count}")
    
    for rec in processing_log:
        if rec.get('status') == 'completed':
            mused = 'yes' if rec.get('mask_used') else 'no'
            tr_val = rec.get('TR')
            print(f"    [OK] {os.path.basename(rec['input'])} | TR={tr_val} | mask_used={mused}")
        else:
            print(f"    [FAIL] {os.path.basename(rec['input'])} | error={rec.get('error')}")
    
    # Write processing log CSV
    log_csv = os.path.join(session_dir, 'processing_log.csv')
    with open(log_csv, 'w', newline='') as f:
        fieldnames = ['input', 'status', 'output_dir', 'mask_used', 'mask_path', 'TR', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in processing_log:
            writer.writerow(rec)
    print(f"\nProcessing log saved to: {log_csv}")
    
    print(f"\n{'='*80}")
    print(f"COMPLETED! Processed {len(all_metrics)} datasets")
    print(f"Output directory: {session_dir}")
    print(f"{'='*80}")
