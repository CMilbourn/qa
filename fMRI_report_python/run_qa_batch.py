#!/usr/bin/env python
"""
Wrapper script to run fMRI QA analysis on multiple subjects/visits
Usage examples:
    python run_qa_batch.py --subject sub001 --visit visit001 --session ses001
    python run_qa_batch.py --base_path /path/to/data --subject sub002 --visit visit002
    python run_qa_batch.py --config config.txt
    python run_qa_batch.py --help
"""

import argparse
import os
import sys
from pathlib import Path
import configparser

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main QA functions
from qa_run_nophase import load_data, find_mask_file, process_data_nophase
import numpy as np
from glob import glob

def run_qa_analysis(base_path, subject, visit, session=None, task='rest', extension='.nii.gz'):
    """
    Run QA analysis for a specific subject/visit combination
    
    Parameters:
    -----------
    base_path : str
        Base path to the BIDS dataset
    subject : str
        Subject identifier (e.g., 'sub001')
    visit : str
        Visit identifier (e.g., 'visit001')
    session : str, optional
        Session identifier (e.g., 'ses001')
    task : str
        Task name (default: 'rest')
    extension : str
        File extension (default: '.nii.gz')
    """
    
    # Construct paths
    if session:
        mypathname = os.path.join(base_path, subject, f"{subject}-{visit}/")
        if session:
            filename_pattern = f'*-{session}-task-{task}-bold'
        else:
            filename_pattern = f'*task-{task}-bold'
    else:
        mypathname = os.path.join(base_path, subject, f"{subject}-{visit}/")
        filename_pattern = f'*task-{task}-bold'
    
    pathname_m = os.path.join(mypathname, 'func/')
    
    print(f"Analyzing: {subject}, {visit}")
    print(f"Looking in: {pathname_m}")
    print(f"Pattern: {filename_pattern + extension}")
    
    # Check if directory exists
    if not os.path.exists(pathname_m):
        print(f"ERROR: Directory does not exist: {pathname_m}")
        return False
        
    # Find files matching the pattern
    core_filenames = set(
        os.path.splitext(os.path.splitext(os.path.basename(file_path))[0])[0]
        for file_path in glob(os.path.join(pathname_m, filename_pattern + extension))
    )
    
    files_found = glob(os.path.join(pathname_m, filename_pattern + extension))
    print(f"Files found: {files_found}")
    print(f"Core filenames: {core_filenames}")
    
    if not core_filenames:
        print(f"ERROR: No files found matching pattern {filename_pattern + extension}")
        return False
    
    # Process each file found
    success_count = 0
    for core_filename in core_filenames:
        try:
            print(f"\nProcessing: {core_filename}")
            
            # Create output directory
            output_directory = os.path.join(mypathname, f'qa_output_{core_filename}')
            os.makedirs(output_directory, exist_ok=True)
            output_dir = os.path.abspath(output_directory)
            print(f"Output directory: {output_dir}")
            
            # Load data
            mag_file_path = os.path.join(pathname_m, core_filename + extension)
            print(f"Loading: {mag_file_path}")
            
            if not os.path.exists(mag_file_path):
                print(f"ERROR: File not found: {mag_file_path}")
                continue
                
            imgm_cla, imgm_cla_affine = load_data(mag_file_path)
            
            # Look for mask file
            mask_path = find_mask_file(pathname_m)
            if mask_path:
                print(f"Found mask: {mask_path}")
                mask_data, mask_affine = load_data(mask_path)
            else:
                print("No mask file found.")
                mask_data = None
            
            # Run QA analysis
            process_data_nophase(imgm_cla, imgm_cla_affine, core_filename, output_dir, mask_data, TR=None, nifti_path=mag_file_path)
            print(f"✓ Successfully processed: {core_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"ERROR processing {core_filename}: {str(e)}")
            continue
    
    print(f"\nCompleted: {success_count}/{len(core_filenames)} files processed successfully")
    return success_count > 0

def read_config_file(config_path):
    """Read configuration from file"""
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def main():
    parser = argparse.ArgumentParser(
        description='Run fMRI QA analysis on BIDS-formatted data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_qa_batch.py --subject sub001 --visit visit001 --session ses001
  python run_qa_batch.py --base_path /path/to/data --subject sub002 --visit visit002
  python run_qa_batch.py --config subjects.txt
  
Config file format (subjects.txt):
  [DEFAULT]
  base_path = /Users/user/data
  extension = .nii.gz
  task = rest
  
  [sub001]
  visit = visit001
  session = ses001
  
  [sub002] 
  visit = visit002
        """
    )
    
    parser.add_argument('--base_path', 
                        default='/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev',
                        help='Base path to BIDS dataset')
    parser.add_argument('--subject', help='Subject ID (e.g., sub001)')
    parser.add_argument('--visit', help='Visit ID (e.g., visit001)')
    parser.add_argument('--session', help='Session ID (e.g., ses001)', default=None)
    parser.add_argument('--task', default='rest', help='Task name (default: rest)')
    parser.add_argument('--extension', default='.nii.gz', help='File extension (default: .nii.gz)')
    parser.add_argument('--config', help='Config file with subject/visit combinations')
    
    args = parser.parse_args()
    
    if args.config:
        # Process from config file
        if not os.path.exists(args.config):
            print(f"ERROR: Config file not found: {args.config}")
            return 1
            
        config = read_config_file(args.config)
        base_path = config.get('DEFAULT', 'base_path', fallback=args.base_path)
        extension = config.get('DEFAULT', 'extension', fallback=args.extension)
        task = config.get('DEFAULT', 'task', fallback=args.task)
        
        total_success = 0
        total_subjects = 0
        
        for subject in config.sections():
            if subject == 'DEFAULT':
                continue
                
            visit = config.get(subject, 'visit')
            session = config.get(subject, 'session', fallback=None)
            
            print(f"\n{'='*50}")
            print(f"Processing {subject}")
            print(f"{'='*50}")
            
            success = run_qa_analysis(base_path, subject, visit, session, task, extension)
            if success:
                total_success += 1
            total_subjects += 1
        
        print(f"\n{'='*50}")
        print(f"SUMMARY: {total_success}/{total_subjects} subjects processed successfully")
        return 0 if total_success > 0 else 1
        
    else:
        # Single subject processing
        if not args.subject or not args.visit:
            print("ERROR: --subject and --visit are required when not using --config")
            parser.print_help()
            return 1
            
        success = run_qa_analysis(args.base_path, args.subject, args.visit, 
                                 args.session, args.task, args.extension)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())