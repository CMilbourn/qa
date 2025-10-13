#!/usr/bin/env python
"""
Modified QA functions to return metrics for PowerPoint generation
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from glob import glob
import json

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main QA functions
try:
    from qa_run_nophase import load_data, find_mask_file
    import qa_run_nophase as qa
    from fMRI_report_python.functions import snr
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def get_tr_from_json(nifti_path):
    """Extract TR from corresponding JSON file"""
    try:
        json_path = nifti_path.replace('.nii.gz', '.json').replace('.nii', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                metadata = json.load(f)
                tr = metadata.get('RepetitionTime')
                if tr:
                    return float(tr)
    except Exception as e:
        print(f"Warning: Could not read TR from JSON: {e}")
    return None

def get_ernst_scaling(tr):
    """Get Ernst angle scaling factor based on TR"""
    if tr is None:
        return 1.0
    if tr <= 0.7:
        return 0.5745  # sin(35°)
    elif tr <= 1.0:
        return 0.7071  # sin(45°)
    elif tr <= 1.5:
        return 0.8155  # sin(54.7°)
    else:
        return 1.0     # sin(90°)

def process_data_with_metrics(imgm_cla, imgm_affine, core_filename, output_dir, 
                             mask_data=None, TR=None, nifti_path=None):
    """
    Modified process_data_nophase that returns QA metrics
    Returns dictionary with all key metrics
    """
    
    print(f"Processing {core_filename} with TR={TR}")
    
    # Apply Ernst angle scaling if TR is provided
    ernst_factor = get_ernst_scaling(TR) if TR else 1.0
    if ernst_factor != 1.0:
        print(f"Applying Ernst scaling factor: {ernst_factor:.4f}")
        imgm_cla = imgm_cla * ernst_factor
    
    # Initialize metrics dictionary
    metrics = {
        'filename': core_filename,
        'tr': TR if TR else 'Unknown',
        'ernst_factor': ernst_factor,
        'shape': imgm_cla.shape,
        'processing_successful': True
    }
    
    try:
        # Basic setup from original function
        time_point = 0
        slice_index = imgm_cla.shape[2] // 2
        slice_index_sag = imgm_cla.shape[0] // 2  
        slice_index_cor = imgm_cla.shape[1] // 2
        
        # Calculate number of rows and columns for montage
        num_slices = imgm_cla.shape[2]
        cols = int(np.ceil(np.sqrt(num_slices)))
        rows = int(np.ceil(num_slices / cols))
        
        # Mean image calculation
        mean_img = np.mean(imgm_cla, axis=-1)
        metrics['mean_intensity'] = np.mean(mean_img)
        
        # Noise volume and masking
        noise_volume = imgm_cla[:, :, :, -1]
        noise_volume = np.nan_to_num(noise_volume, nan=0.0)
        
        tmean_img = np.mean(imgm_cla, axis=-1)
        brain_mask = tmean_img > (0.05 * np.max(tmean_img))
        masked_noise = noise_volume * brain_mask
        
        # Calculate iSNR
        print("Calculating iSNR...")
        isnr_obj_cla = snr.Isnr(imgm_cla, imgm_affine, noise_mask=masked_noise)
        isnr_value = np.mean(isnr_obj_cla.isnr)
        noise_value = np.mean(isnr_obj_cla.noise)
        
        metrics['isnr'] = float(isnr_value)
        metrics['noise_value'] = float(noise_value)
        print(f'iSNR: {isnr_value:.2f}')
        
        # Save iSNR NIFTI
        isnr_obj_cla.to_nifti(output_dir, 'isnr')
        
        # Calculate tSNR (remove noise scan)
        print("Calculating tSNR...")
        imgm_cla_nn = imgm_cla[:, :, :, :-1]
        tsnr_obj_cla = snr.Tsnr(imgm_cla_nn, imgm_affine)
        tsnr_obj_cla.to_nifti(output_dir, 'tsnr')
        
        mean_tsnr = np.mean(tsnr_obj_cla.tsnr_map)
        metrics['tsnr'] = float(mean_tsnr)
        print(f'Mean tSNR: {mean_tsnr:.2f}')
        
        # tSNR per unit time
        if TR:
            tsnr_per_unit = mean_tsnr / np.sqrt(TR)
            metrics['tsnr_per_unit_time'] = float(tsnr_per_unit)
            print(f'tSNR per unit time: {tsnr_per_unit:.2f}')
        else:
            metrics['tsnr_per_unit_time'] = None
        
        # Masked tSNR if mask is available
        if mask_data is not None:
            print("Calculating masked tSNR...")
            masked_tsnr = tsnr_obj_cla.tsnr_map[mask_data > 0]
            metrics['masked_tsnr'] = float(np.mean(masked_tsnr))
            print(f'Mean tSNR in mask: {metrics["masked_tsnr"]:.2f}')
        else:
            metrics['masked_tsnr'] = None
        
        # Calculate SSN (Spatial Signal-to-Noise) - simplified version
        signal_mean = np.mean(mean_img[brain_mask])
        signal_std = np.std(mean_img[brain_mask])
        ssn = signal_mean / signal_std if signal_std > 0 else 0
        metrics['ssn'] = float(ssn)
        
        print(f"✅ Metrics calculated successfully")
        
        # Now call the original processing function for image generation
        # Import and call the original function
        from qa_run_nophase import process_data_nophase
        process_data_nophase(imgm_cla, imgm_affine, core_filename, output_dir, 
                           mask_data, TR=TR, nifti_path=nifti_path)
        
    except Exception as e:
        print(f"❌ Error calculating metrics: {e}")
        metrics['processing_successful'] = False
        metrics['error'] = str(e)
        # Still try to run basic processing
        try:
            from qa_run_nophase import process_data_nophase
            process_data_nophase(imgm_cla, imgm_affine, core_filename, output_dir, 
                               mask_data, TR=TR, nifti_path=nifti_path)
        except Exception as e2:
            print(f"❌ Original processing also failed: {e2}")
    
    return metrics

def run_qa_with_metrics(func_dir, pattern='*fmri*', extension='.nii.gz'):
    """
    Run QA analysis and return metrics for each file
    Returns list of (output_directory, metrics_dict) tuples
    """
    
    print(f"🔍 fMRI QA Analysis with Metrics Collection")
    print(f"📁 Directory: {func_dir}")
    print(f"🔎 Pattern: {pattern}{extension}")
    
    # Check if directory exists
    if not os.path.exists(func_dir):
        print(f"❌ ERROR: Directory does not exist: {func_dir}")
        return []
    
    # Find files matching the pattern
    search_pattern = os.path.join(func_dir, pattern + extension)
    files_found = glob(search_pattern)
    
    if not files_found:
        print(f"❌ ERROR: No files found matching pattern {search_pattern}")
        return []
    
    print(f"📋 Found {len(files_found)} files to process")
    
    results = []
    
    for i, file_path in enumerate(files_found, 1):
        try:
            core_filename = os.path.splitext(os.path.splitext(os.path.basename(file_path))[0])[0]
            
            print(f"\n{'='*60}")
            print(f"🔄 Processing {i}/{len(files_found)}: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            # Get TR from JSON
            detected_tr = get_tr_from_json(file_path)
            
            # Create output directory
            parent_dir = os.path.dirname(func_dir)
            output_directory = os.path.join(parent_dir, f'qa_output_{core_filename}')
            os.makedirs(output_directory, exist_ok=True)
            output_dir = os.path.abspath(output_directory)
            
            # Load data
            print(f"📥 Loading data...")
            imgm_cla, imgm_cla_affine = load_data(file_path)
            
            # Look for mask
            mask_path = find_mask_file(func_dir)
            mask_data = None
            if mask_path:
                print(f"🎭 Found mask: {os.path.basename(mask_path)}")
                mask_data, _ = load_data(mask_path)
            
            # Process with metrics collection
            metrics = process_data_with_metrics(imgm_cla, imgm_cla_affine, core_filename, 
                                              output_dir, mask_data, TR=detected_tr, 
                                              nifti_path=file_path)
            
            results.append((output_dir, metrics))
            print(f"✅ Completed: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"❌ ERROR processing {file_path}: {str(e)}")
            continue
    
    print(f"\n🎉 Analysis Complete: {len(results)}/{len(files_found)} files processed")
    return results