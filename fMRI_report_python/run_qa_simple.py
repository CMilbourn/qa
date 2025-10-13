#!/usr/bin/env python
"""
Simple wrapper for fMRI QA analysis - handles non-BIDS structures
Usage: python run_qa_simple.py --func_dir /path/to/func/directory [--pattern pattern] [--extension .nii.gz]
"""

import argparse
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main QA functions
from qa_run_nophase import load_data, find_mask_file, process_data_nophase
import numpy as np
from glob import glob

def run_qa_simple(func_dir, pattern='*bold*', extension='.nii.gz'):
    """
    Run QA analysis for a simple directory structure
    
    Parameters:
    -----------
    func_dir : str
        Path to the func directory containing the BOLD files
    pattern : str
        Filename pattern to match (default: '*bold*')
    extension : str
        File extension (default: '.nii.gz')
    """
    
    print(f"Analyzing directory: {func_dir}")
    print(f"Looking for files matching: {pattern}{extension}")
    
    # Check if directory exists
    if not os.path.exists(func_dir):
        print(f"ERROR: Directory does not exist: {func_dir}")
        return False
    
    # Find files matching the pattern
    search_pattern = os.path.join(func_dir, pattern + extension)
    files_found = glob(search_pattern)
    
    print(f"Files found: {files_found}")
    
    if not files_found:
        print(f"ERROR: No files found matching pattern {search_pattern}")
        return False
    
    # Process each file found
    success_count = 0
    for file_path in files_found:
        try:
            # Extract core filename
            core_filename = os.path.splitext(os.path.splitext(os.path.basename(file_path))[0])[0]
            print(f"\nProcessing: {core_filename}")
            
            # Create output directory in the same parent directory as func
            parent_dir = os.path.dirname(func_dir)
            output_directory = os.path.join(parent_dir, f'qa_output_{core_filename}')
            os.makedirs(output_directory, exist_ok=True)
            output_dir = os.path.abspath(output_directory)
            print(f"Output directory: {output_dir}")
            
            # Load data
            print(f"Loading: {file_path}")
            if not os.path.exists(file_path):
                print(f"ERROR: File not found: {file_path}")
                continue
                
            imgm_cla, imgm_cla_affine = load_data(file_path)
            
            # Look for mask file in the same directory
            mask_path = find_mask_file(func_dir)
            if mask_path:
                print(f"Found mask: {mask_path}")
                mask_data, mask_affine = load_data(mask_path)
            else:
                print("No mask file found.")
                mask_data = None
            
            # Run QA analysis
            process_data_nophase(imgm_cla, imgm_cla_affine, core_filename, output_dir, mask_data)
            print(f"✓ Successfully processed: {core_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"ERROR processing {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\nCompleted: {success_count}/{len(files_found)} files processed successfully")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(
        description='Run fMRI QA analysis on a single func directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_qa_simple.py --func_dir /path/to/sub003/func/
  python run_qa_simple.py --func_dir /path/to/sub003/func/ --pattern '*task-rest*'
  python run_qa_simple.py --func_dir /path/to/sub003/func/ --pattern '*bold*' --extension .nii
        """
    )
    
    parser.add_argument('--func_dir', required=True,
                        help='Path to the func directory containing BOLD files')
    parser.add_argument('--pattern', default='*bold*',
                        help='Filename pattern to match (default: *bold*)')
    parser.add_argument('--extension', default='.nii.gz',
                        help='File extension (default: .nii.gz)')
    
    args = parser.parse_args()
    
    success = run_qa_simple(args.func_dir, args.pattern, args.extension)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())