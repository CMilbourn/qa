#!/usr/bin/env python
"""
Updated version of qa_run_nophase.py with automatic TR detection from JSON files
"""

import sys
sys.path.append('/Users/cmilbourn/Documents/GitHub/qa/')

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import Normalize
import nibabel as nib
from glob import glob
import subprocess
import json

#from ukat.data import fetch
from fMRI_report_python.functions import snr
from scipy.signal import detrend
from mpl_toolkits.mplot3d import Axes3D

# check packages
print(snr)
print(dir(snr))

def load_data(inputdatafilename):
    """Function to load in data"""
    data = nib.load(inputdatafilename)
    image = data.get_fdata()
    return image, data.affine

def find_mask_file(directory):
    """Function to find a file containing 'mask' in its name"""
    for filename in os.listdir(directory):
        if "mask" in filename.lower() and filename.endswith(('.nii', '.nii.gz')):
            return os.path.join(directory, filename)
    return None

def get_tr_from_json(nifti_path):
    """
    Read RepetitionTime from BIDS JSON sidecar file
    
    Parameters:
    -----------
    nifti_path : str
        Path to the NIfTI file
        
    Returns:
    --------
    float or None
        RepetitionTime in seconds, or None if not found
    """
    json_path = nifti_path.replace('.nii.gz', '.json').replace('.nii', '.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            tr = metadata.get('RepetitionTime')
            if tr is not None:
                print(f"✓ Found TR = {tr}s in JSON file: {os.path.basename(json_path)}")
                return float(tr)
            else:
                print(f"⚠ RepetitionTime not found in JSON file: {os.path.basename(json_path)}")
                return None
                
        except Exception as e:
            print(f"✗ Error reading JSON file {json_path}: {e}")
            return None
    else:
        print(f"ⓘ No JSON sidecar found for: {os.path.basename(nifti_path)}")
        return None

def get_ernst_scaling(TR):
    """
    Get Ernst angle scaling factor based on TR
    These are approximate values for typical T1 relaxation times
    """
    if TR <= 0.7:
        return 0.5745  # For very short TR
    elif TR <= 1.0:
        return 0.7071  # For short TR  
    elif TR <= 1.5:
        return 0.8155  # For medium TR
    else:
        return 1.0     # For longer TR (TR >= 2s, T1 = 2132ms)

def process_data_nophase(imgm_cla, imgm_affine, core_filename, output_dir, 
                        mask_data=None, TR=None, nifti_path=None):
    """
    Main QA processing function with automatic TR detection
    """
    
    # Determine TR from JSON file if not provided
    if TR is None and nifti_path is not None:
        TR = get_tr_from_json(nifti_path)
    
    if TR is None:
        TR = 1.4  # Default for MB3 BOLD data
        print(f"ⓘ Using default TR = {TR}s (no JSON file found or RepetitionTime not specified)")
    else:
        print(f"✓ Using TR = {TR}s from JSON metadata")
    
    # Set Ernst angle scaling factor
    ErnstScaling = get_ernst_scaling(TR)
    print(f"ⓘ Ernst scaling factor = {ErnstScaling} for TR = {TR}s")
    
    # [Rest of the processing function - copying from original]
    ############################## Plotting mean images
    slice_index = 12
    slice_index_sag = 50
    slice_index_cor = 50
    print(f"Slice index: {slice_index}")
    time_point = 1
    tsnrScale = 100
    isnrScale = 100

    # ROI parameters
    x_start = 60
    y_start = 80
    roi_width = 20
    roi_height = 20

    mean_img = np.mean(imgm_cla, axis=3)
    
    # Create mean image plot
    fig, axs = plt.subplots(1, 1, figsize=(5, 5))
    axs.imshow(mean_img[:, :, slice_index].T, origin='lower', cmap='gray')
    axs.set_title(f'Magnitude (Slice {slice_index})')
    axs.axis(False)
    plt.tight_layout()
    
    output_filename = 'Mean_image.png'
    output_path = f"{output_dir}/{output_filename}"
    fig.savefig(output_path, dpi=300)
    plt.close()

    # Montage of mean images
    num_slices = imgm_cla.shape[2]
    rows = int(np.ceil(np.sqrt(num_slices)))
    cols = int(np.ceil(num_slices / rows))
    
    figsize_scale = 2.5
    fig = plt.figure(figsize=(cols * figsize_scale, rows * figsize_scale))
    
    vmin = np.percentile(mean_img, 2)
    vmax = np.percentile(mean_img, 98)
    
    for i in range(num_slices):
        ax = fig.add_subplot(rows, cols, i + 1)
        ax.imshow(mean_img[:, :, i], cmap='gray', vmin=vmin, vmax=vmax)
        ax.set_title(f"Slice {i}", fontsize=8)
        ax.axis('off')
    
    fig.tight_layout(pad=0.3)
    output_path = f"{output_dir}/mean_montage.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    ############################## iSNR calculation
    noise_volume = imgm_cla[:, :, :, -1]
    noise_volume = np.nan_to_num(noise_volume, nan=0.0)
    
    # Create brain mask
    tmean_img = np.mean(imgm_cla, axis=-1)
    brain_mask = tmean_img > (0.05 * np.max(tmean_img))
    masked_noise = noise_volume * brain_mask
    masked_mean = mean_img * brain_mask
    valid_voxels = masked_mean[masked_mean != 0]
    mean_std = np.std(valid_voxels)
    print(f'Mean volume std = {mean_std:.2f}.')
    
    # Plot noise analysis
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    im1 = axs[0].imshow(noise_volume[:, :, slice_index].T, origin='lower', cmap='viridis')
    axs[0].set_title("Noise Volume")
    axs[0].axis(False)
    fig.colorbar(im1, ax=axs[0])
    
    im2 = axs[1].imshow(brain_mask[:, :, slice_index].T, origin='lower', cmap='gray')
    axs[1].set_title("Brain Mask")
    axs[1].axis(False)
    fig.colorbar(im2, ax=axs[1])
    
    im3 = axs[2].imshow(masked_noise[:, :, slice_index].T, origin='lower', cmap='viridis')
    axs[2].set_title("Masked Noise")
    axs[2].axis(False)
    fig.colorbar(im3, ax=axs[2])
    
    plt.tight_layout()
    fig.savefig(f"{output_dir}/masked_noise.png", dpi=300)
    plt.close()
    
    # Calculate iSNR
    isnr_obj_cla = snr.Isnr(imgm_cla, imgm_affine, noise_mask=masked_noise)
    isnr_obj_cla.to_nifti(output_dir, 'isnr')
    print(f'Image has an iSNR of {np.mean(isnr_obj_cla.isnr):.2f}.')
    print(f'Noise value used for iSNR: {np.mean(isnr_obj_cla.noise):.2f}')

    ############################## tSNR calculation
    imgm_cla_nn = imgm_cla[:, :, :, :-1]  # Remove noise scan
    
    tsnr_obj_cla = snr.Tsnr(imgm_cla_nn, imgm_affine)
    tsnr_obj_cla.to_nifti(output_dir, 'tsnr')

    print(f"tSNR map shape: {tsnr_obj_cla.tsnr_map.shape}")
    my_mean_tsnr = np.mean(tsnr_obj_cla.tsnr_map)
    print(f"Mean tSNR: {my_mean_tsnr:.2f}")

    if mask_data is not None:
        tsnr_threshold = np.percentile(tsnr_obj_cla.tsnr_map[mask_data > 0], 50)
        voxels_to_plot = (tsnr_obj_cla.tsnr_map > tsnr_threshold) & (mask_data > 0)
        print("Found mask")
        masked_tSNR = tsnr_obj_cla.tsnr_map[mask_data > 0]
        print(f"Mean tSNR in mask: {np.mean(masked_tSNR):.2f}")

    #### tSNR per unit time (using detected TR) ######
    tsnr_unit_time_map = (tsnr_obj_cla.tsnr_map / np.sqrt(TR)) * ErnstScaling
    
    # Save the new map as NIfTI
    tsnr_unit_time_img = nib.Nifti1Image(tsnr_unit_time_map, affine=imgm_affine)
    nib.save(tsnr_unit_time_img, f"{output_dir}/tsnr_unit_time.nii.gz")
    
    mean_tsnr_unit_time = np.mean(tsnr_unit_time_map)
    print(f"Mean tSNR per unit time: {mean_tsnr_unit_time:.2f}")
    
    # Save tSNR plots
    fig_ut, axs_ut = plt.subplots(1, 1, figsize=(8, 8))
    im_ut = axs_ut.imshow(np.rot90(tsnr_unit_time_map[:, :, slice_index]), cmap='inferno', clim=(0, tsnrScale))
    axs_ut.set_title(f'tSNR per unit time (TR={TR}s, slc {slice_index})')
    axs_ut.axis(False)
    cb_ut = fig_ut.colorbar(im_ut, ax=axs_ut, shrink=0.6)
    cb_ut.set_label('tSNR / √TR')
    fig_ut.tight_layout()
    fig_ut.savefig(f"{output_dir}/tSNR_per_unit_time.png", dpi=300)
    plt.close(fig_ut)

    # Raw tSNR plot
    fig_raw, axs_raw = plt.subplots(1, 1, figsize=(8, 8))
    im_raw = axs_raw.imshow(np.rot90(tsnr_obj_cla.tsnr_map[:, :, slice_index]), cmap='inferno', clim=(0, tsnrScale))
    axs_raw.set_title(f'Raw tSNR (TR={TR}s, slc {slice_index})')
    axs_raw.axis(False)
    cb_raw = fig_raw.colorbar(im_raw, ax=axs_raw, shrink=0.6)
    cb_raw.set_label('tSNR')
    fig_raw.tight_layout()
    fig_raw.savefig(f"{output_dir}/tSNR_raw.png", dpi=300)
    plt.close(fig_raw)

    print("✓ QA analysis completed successfully!")
    print(f"✓ TR = {TR}s (Ernst scaling = {ErnstScaling})")
    print(f"✓ Output saved to: {output_dir}")

def run_qa_analysis_with_tr_detection(nifti_file, output_dir=None, mask_file=None):
    """
    Simplified function to run QA with automatic TR detection
    """
    if output_dir is None:
        base_name = os.path.splitext(os.path.splitext(os.path.basename(nifti_file))[0])[0]
        output_dir = os.path.join(os.path.dirname(nifti_file), f"qa_output_{base_name}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing: {nifti_file}")
    print(f"Output directory: {output_dir}")
    
    # Load data
    imgm_cla, imgm_affine = load_data(nifti_file)
    
    # Load mask if provided
    mask_data = None
    if mask_file and os.path.exists(mask_file):
        print(f"Loading mask: {mask_file}")
        mask_data, _ = load_data(mask_file)
    
    # Get core filename
    core_filename = os.path.splitext(os.path.splitext(os.path.basename(nifti_file))[0])[0]
    
    # Run QA with TR auto-detection
    process_data_nophase(imgm_cla, imgm_affine, core_filename, output_dir, 
                        mask_data=mask_data, TR=None, nifti_path=nifti_file)

if __name__ == "__main__":
    # Example usage - replace with your file path
    nifti_file = "/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001-ses001-task-rest-bold.nii.gz"
    
    if len(sys.argv) > 1:
        nifti_file = sys.argv[1]
    
    if os.path.exists(nifti_file):
        run_qa_analysis_with_tr_detection(nifti_file)
    else:
        print(f"File not found: {nifti_file}")
        print("Usage: python qa_with_tr_detection.py <path_to_nifti_file>")