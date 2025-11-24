#!/usr/bin/env python
"""
Batch QA processor for multiple files with different TRs in a single directory
Usage: python run_qa_multi_tr.py --func_dir /path/to/func/ [--pattern pattern]
"""

import argparse
import os
import sys
from pathlib import Path
import time

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main QA functions
from qa_run_nophase import load_data, find_mask_file, process_data_nophase
from qa_with_tr_detection import get_tr_from_json, get_ernst_scaling
import numpy as np
from glob import glob
import json

def run_multi_tr_analysis(func_dir, pattern='*fmri*', extension='.nii.gz'):
    """
    Run QA analysis on multiple files with different TRs in a directory
    
    Parameters:
    -----------
    func_dir : str
        Path to the func directory containing the BOLD files
    pattern : str
        Filename pattern to match (default: '*fmri*')
    extension : str
        File extension (default: '.nii.gz')
    """
    
    print(f"🔍 Analyzing directory: {func_dir}")
    print(f"📁 Looking for files matching: {pattern}{extension}")
    
    # Check if directory exists
    if not os.path.exists(func_dir):
        print(f"❌ ERROR: Directory does not exist: {func_dir}")
        return False
    
    # Find files matching the pattern
    search_pattern = os.path.join(func_dir, pattern + extension)
    files_found = glob(search_pattern)
    
    print(f"📋 Files found: {len(files_found)}")
    for i, f in enumerate(files_found, 1):
        print(f"   {i}. {os.path.basename(f)}")
    
    if not files_found:
        print(f"❌ ERROR: No files found matching pattern {search_pattern}")
        return False
    
    # Analyze TR values first
    print(f"\n🕐 Checking TR values in JSON files:")
    tr_info = []
    for file_path in files_found:
        tr = get_tr_from_json(file_path)
        tr_info.append((file_path, tr))
        basename = os.path.basename(file_path)
        if tr:
            ernst = get_ernst_scaling(tr)
            print(f"   📊 {basename[:50]}... → TR = {tr}s (Ernst = {ernst})")
        else:
            print(f"   ⚠️  {basename[:50]}... → TR = default (no JSON)")
    
    print(f"\n🚀 Starting QA processing of {len(files_found)} files...\n")
    
    # Process each file found
    success_count = 0
    total_files = len(files_found)
    
    for i, (file_path, detected_tr) in enumerate(tr_info, 1):
        try:
            # Extract core filename
            core_filename = os.path.splitext(os.path.splitext(os.path.basename(file_path))[0])[0]
            
            print(f"{'='*60}")
            print(f"🔄 Processing file {i}/{total_files}")
            print(f"📄 File: {os.path.basename(file_path)}")
            if detected_tr:
                ernst = get_ernst_scaling(detected_tr)
                print(f"🕐 TR: {detected_tr}s (Ernst scaling: {ernst})")
            else:
                print(f"🕐 TR: Using default (1.4s)")
            print(f"{'='*60}")
            
            # Create output directory in the parent of func directory
            parent_dir = os.path.dirname(func_dir)
            output_directory = os.path.join(parent_dir, f'qa_output_{core_filename}')
            os.makedirs(output_directory, exist_ok=True)
            output_dir = os.path.abspath(output_directory)
            print(f"📂 Output directory: {output_dir}")
            
            # Load data
            print(f"📥 Loading data...")
            if not os.path.exists(file_path):
                print(f"❌ ERROR: File not found: {file_path}")
                continue
                
            imgm_cla, imgm_cla_affine = load_data(file_path)
            print(f"✅ Loaded data shape: {imgm_cla.shape}")
            
            # Look for mask file in the same directory
            mask_path = find_mask_file(func_dir)
            if mask_path:
                print(f"🎭 Found mask: {os.path.basename(mask_path)}")
                mask_data, mask_affine = load_data(mask_path)
            else:
                print(f"ℹ️  No mask file found")
                mask_data = None
            
            # Record start time
            start_time = time.time()
            
            # Run QA analysis
            print(f"🔬 Running QA analysis...")
            process_data_nophase(imgm_cla, imgm_cla_affine, core_filename, output_dir, 
                                mask_data, TR=detected_tr, nifti_path=file_path)
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Successfully processed: {core_filename}")
            print(f"⏱️  Processing time: {processing_time:.1f} seconds")
            success_count += 1
            
        except Exception as e:
            print(f"❌ ERROR processing {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print(f"🎉 BATCH PROCESSING COMPLETE")
    print(f"✅ Successfully processed: {success_count}/{total_files} files")
    
    if success_count > 0:
        print(f"📂 Output directories created in: {os.path.dirname(func_dir)}/qa_output_*")
        
        # Show summary of TR values processed
        unique_trs = set([tr for _, tr in tr_info if tr is not None])
        if unique_trs:
            print(f"🕐 TR values processed: {sorted(unique_trs)} seconds")
    
    print(f"{'='*60}")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(
        description='Run fMRI QA analysis on multiple files with different TRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_qa_multi_tr.py --func_dir /path/to/sub003/func/
  python run_qa_multi_tr.py --func_dir /path/to/func/ --pattern '*bold*'
  python run_qa_multi_tr.py --func_dir /path/to/func/ --pattern '*task-rest*'
        """
    )
    
    parser.add_argument('--func_dir', required=True,
                        help='Path to the func directory containing BOLD files')
    parser.add_argument('--pattern', default='*fmri*',
                        help='Filename pattern to match (default: *fmri*)')
    parser.add_argument('--extension', default='.nii.gz',
                        help='File extension (default: .nii.gz)')
    
    args = parser.parse_args()
    
    success = run_multi_tr_analysis(args.func_dir, args.pattern, args.extension)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())