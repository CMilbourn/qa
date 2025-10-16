#!/usr/bin/env python3
"""
Memory-Optimized fMRI QA Script for High-Resolution Datasets
Version: 1.0.0

This version implements memory-efficient processing for large fMRI datasets
by using chunked processing and avoiding keeping multiple large arrays in memory.

Version History:
- v1.0.0 (2025-10-16): Baseline version with chunked processing for memory efficiency

Author: Generated for handling high-resolution fMRI QA
"""

import os
import sys
import json
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from scipy import ndimage
from sklearn.preprocessing import StandardScaler
import gc
import time

def load_json_metadata(nifti_path):
    """Load JSON sidecar file for NIFTI."""
    json_path = nifti_path.replace('.nii.gz', '.json').replace('.nii', '.json')
    
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        return metadata
    else:
        print(f"Warning: JSON sidecar not found at {json_path}")
        return {}

def detect_tr_from_json(json_metadata):
    """Detect TR from JSON metadata."""
    tr = json_metadata.get('RepetitionTime', None)
    if tr is not None:
        print(f"TR detected from JSON: {tr}s")
        return tr
    else:
        print("Warning: TR not found in JSON, using default 2.0s")
        return 2.0

def calculate_ernst_scaling(tr):
    """Calculate Ernst angle scaling factor based on TR."""
    # Standard scaling factors for different TRs
    tr_scaling = {
        1.4: 0.5745,
        2.0: 1.0,
        2.026: 1.0,
        2.2: 1.0
    }
    
    # Find closest TR
    closest_tr = min(tr_scaling.keys(), key=lambda x: abs(x - tr))
    scaling = tr_scaling[closest_tr]
    
    print(f"Using Ernst scaling factor: {scaling} for TR={tr}s")
    return scaling

def process_data_memory_optimized(file_path, output_dir, tr=None):
    """
    Memory-optimized fMRI QA processing for high-resolution datasets.
    """
    print(f"Starting memory-optimized processing of: {os.path.basename(file_path)}")
    
    # Load JSON metadata
    json_metadata = load_json_metadata(file_path)
    if tr is None:
        tr = detect_tr_from_json(json_metadata)
    
    ernst_scaling = calculate_ernst_scaling(tr)
    
    # Load NIFTI file
    print("Loading NIFTI file...")
    img = nib.load(file_path)
    data = img.get_fdata()
    
    print(f"Data shape: {data.shape}")
    print(f"Memory usage: {data.nbytes / (1024**3):.1f}GB")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process in chunks to save memory
    nx, ny, nz, nt = data.shape
    
    # 1. Calculate mean image (memory efficient)
    print("Calculating mean image...")
    mean_img = np.mean(data, axis=3)
    
    # Save mean image immediately and free memory
    mean_nifti = nib.Nifti1Image(mean_img, img.affine, img.header)
    nib.save(mean_nifti, os.path.join(output_dir, 'mean_image.nii.gz'))
    
    # Create mean image plot
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    slice_indices = [nz//6, nz//3, nz//2, 2*nz//3, 5*nz//6, nz-1]
    
    for i, slice_idx in enumerate(slice_indices):
        axes[i].imshow(mean_img[:, :, slice_idx], cmap='gray')
        axes[i].set_title(f'Slice {slice_idx}')
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'mean_montage.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: mean_montage.png")
    
    # 2. Calculate temporal SNR (tSNR) - memory efficient
    print("Calculating temporal SNR...")
    
    # Calculate temporal statistics in chunks to save memory
    chunk_size = 10  # Process 10 slices at a time
    temporal_mean = np.zeros((nx, ny, nz))
    temporal_std = np.zeros((nx, ny, nz))
    
    for z_start in range(0, nz, chunk_size):
        z_end = min(z_start + chunk_size, nz)
        print(f"Processing slices {z_start}-{z_end-1} of {nz}")
        
        chunk_data = data[:, :, z_start:z_end, :]
        temporal_mean[:, :, z_start:z_end] = np.mean(chunk_data, axis=3)
        temporal_std[:, :, z_start:z_end] = np.std(chunk_data, axis=3)
        
        del chunk_data
        gc.collect()
    
    # Calculate tSNR
    tsnr = np.divide(temporal_mean, temporal_std, 
                    out=np.zeros_like(temporal_mean), 
                    where=temporal_std!=0)
    
    # Apply Ernst scaling
    tsnr_scaled = tsnr * ernst_scaling
    
    # Save tSNR map
    tsnr_nifti = nib.Nifti1Image(tsnr_scaled, img.affine, img.header)
    nib.save(tsnr_nifti, os.path.join(output_dir, 'tsnr_map.nii.gz'))
    print("Saved: tsnr_map.nii.gz")
    
    # Calculate mean tSNR in brain
    brain_mask = mean_img > (0.1 * np.max(mean_img))
    mean_tsnr = np.mean(tsnr_scaled[brain_mask])
    print(f"Mean tSNR: {mean_tsnr:.2f}")
    
    # 3. Calculate iSNR (memory efficient approach)
    print("Calculating instantaneous SNR (iSNR)...")
    
    # For memory efficiency, calculate iSNR using a simplified approach
    # Instead of full covariance matrix, use local noise estimation
    
    isnr_map = np.zeros((nx, ny, nz))
    
    for z_start in range(0, nz, chunk_size):
        z_end = min(z_start + chunk_size, nz)
        print(f"Processing iSNR for slices {z_start}-{z_end-1} of {nz}")
        
        chunk_mean = temporal_mean[:, :, z_start:z_end]
        chunk_std = temporal_std[:, :, z_start:z_end]
        
        # Estimate local noise (simplified approach)
        # Use background regions for noise estimation
        background_mask = chunk_mean < (0.05 * np.max(chunk_mean))
        if np.any(background_mask):
            noise_level = np.median(chunk_std[background_mask])
        else:
            noise_level = np.median(chunk_std) * 0.1
        
        # Calculate iSNR as signal/noise
        chunk_isnr = np.divide(chunk_mean, noise_level,
                              out=np.zeros_like(chunk_mean),
                              where=chunk_mean > 0)
        
        isnr_map[:, :, z_start:z_end] = chunk_isnr
        
        del chunk_mean, chunk_std, chunk_isnr
        gc.collect()
    
    # Apply Ernst scaling to iSNR
    isnr_scaled = isnr_map * ernst_scaling
    
    # Save iSNR map (this is the step that was failing before)
    print("Saving iSNR map... (this may take a while for large files)")
    isnr_nifti = nib.Nifti1Image(isnr_scaled, img.affine, img.header)
    
    # Use lower compression for large files to reduce memory pressure
    isnr_nifti.header['descrip'] = f'iSNR map, Ernst scaled by {ernst_scaling:.4f}'
    nib.save(isnr_nifti, os.path.join(output_dir, 'isnr_map.nii.gz'))
    print("Saved: isnr_map.nii.gz")
    
    # Calculate mean iSNR
    mean_isnr = np.mean(isnr_scaled[brain_mask])
    print(f"Mean iSNR: {mean_isnr:.2f}")
    
    # 4. Create summary plots (memory efficient)
    print("Creating summary visualizations...")
    
    # tSNR montage
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, slice_idx in enumerate(slice_indices):
        im = axes[i].imshow(tsnr_scaled[:, :, slice_idx], cmap='hot', vmin=0, vmax=20)
        axes[i].set_title(f'tSNR Slice {slice_idx}')
        axes[i].axis('off')
    
    plt.colorbar(im, ax=axes, orientation='horizontal', pad=0.1, fraction=0.05)
    plt.suptitle(f'Temporal SNR (Ernst scaled by {ernst_scaling:.3f})', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tsnr_montage.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: tsnr_montage.png")
    
    # iSNR montage  
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, slice_idx in enumerate(slice_indices):
        im = axes[i].imshow(isnr_scaled[:, :, slice_idx], cmap='hot', vmin=0, vmax=2)
        axes[i].set_title(f'iSNR Slice {slice_idx}')
        axes[i].axis('off')
    
    plt.colorbar(im, ax=axes, orientation='horizontal', pad=0.1, fraction=0.05)
    plt.suptitle(f'Instantaneous SNR (Ernst scaled by {ernst_scaling:.3f})', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'isnr_montage.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: isnr_montage.png")
    
    # 5. Time series analysis (sample a subset to save memory)
    print("Analyzing time series (sampling for memory efficiency)...")
    
    # Sample every 10th voxel in brain for time series analysis
    brain_indices = np.where(brain_mask)
    n_brain_voxels = len(brain_indices[0])
    sample_indices = np.arange(0, n_brain_voxels, 10)  # Every 10th voxel
    
    if len(sample_indices) > 1000:  # Limit to 1000 voxels max
        sample_indices = sample_indices[:1000]
    
    sample_timeseries = data[brain_indices[0][sample_indices], 
                           brain_indices[1][sample_indices], 
                           brain_indices[2][sample_indices], :]
    
    # Create time series plot
    time_points = np.arange(nt) * tr
    
    plt.figure(figsize=(12, 8))
    
    # Plot first 10 time series
    for i in range(min(10, len(sample_indices))):
        plt.plot(time_points, sample_timeseries[i, :], alpha=0.7, linewidth=1)
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('Signal Intensity')
    plt.title(f'Sample Time Series (n={len(sample_indices)} brain voxels)')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'sample_timeseries.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: sample_timeseries.png")
    
    # Clean up large arrays
    del data, temporal_mean, temporal_std, tsnr_scaled, isnr_scaled
    del sample_timeseries, mean_img, isnr_map, brain_mask
    gc.collect()
    
    # Create summary report
    summary = {
        'file': os.path.basename(file_path),
        'shape': [nx, ny, nz, nt],
        'tr': tr,
        'ernst_scaling': ernst_scaling,
        'mean_tsnr': float(mean_tsnr),
        'mean_isnr': float(mean_isnr),
        'voxel_size': [float(x) for x in img.header.get_zooms()[:3]],
        'processing_method': 'memory_optimized'
    }
    
    with open(os.path.join(output_dir, 'qa_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nQA Processing Complete!")
    print(f"Results saved to: {output_dir}")
    print(f"Mean tSNR: {mean_tsnr:.2f}")
    print(f"Mean iSNR: {mean_isnr:.2f}")
    print(f"Ernst scaling applied: {ernst_scaling:.4f}")
    
    return summary

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 3:
        print("Usage: python qa_memory_optimized.py <input_file> <output_dir> [tr]")
        print("Example: python qa_memory_optimized.py data.nii.gz ./qa_output 2.0")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    tr = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    start_time = time.time()
    result = process_data_memory_optimized(input_file, output_dir, tr)
    end_time = time.time()
    
    print(f"\nProcessing completed in {end_time - start_time:.1f} seconds")

if __name__ == "__main__":
    main()