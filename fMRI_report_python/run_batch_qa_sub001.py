#!/usr/bin/env python3
"""
Batch QA Processing for sub001 fMRI Data

Process all three sub001 fMRI files using memory-optimized QA processing.
"""

import os
import sys
import time
import subprocess

# Add the current directory to Python path for imports
sys.path.append('/Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python')

def run_memory_optimized_qa(nifti_file, output_base_dir):
    """Run memory-optimized QA on a single file."""
    
    # Create output directory name from input file
    basename = os.path.basename(nifti_file)
    output_name = basename.replace('.nii.gz', '').replace('.nii', '')
    output_dir = os.path.join(output_base_dir, output_name)
    
    print(f"\n{'='*80}")
    print(f"Processing: {basename}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}")
    
    # Prepare command
    cmd = [
        'bash', '-c',
        f'source /Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python/venv/bin/activate && '
        f'cd /Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python && '
        f'python qa_memory_optimized.py "{nifti_file}" "{output_dir}"'
    ]
    
    start_time = time.time()
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            end_time = time.time()
            print(f"✅ SUCCESS: Processed in {end_time - start_time:.1f} seconds")
            print(result.stdout)
            return True, output_dir
        else:
            print(f"❌ ERROR: Failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, None
            
    except subprocess.TimeoutExpired:
        print(f"❌ ERROR: Processing timed out after 5 minutes")
        return False, None
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")
        return False, None

def main():
    """Main batch processing function."""
    
    # Define the three sub001 files
    func_dir = "/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func"
    
    files_to_process = [
        "sub001-visit001_3315-101_Sweet_02092025_20250902150849_4_fmri_MB3_ARC2_fMRI_2mm.nii.gz",
        "sub001-visit001_3315-101_Sweet_02092025_20250902150849_7_fmri_MB3_ARC2_fMRI_2mm_1.5.nii.gz", 
        "sub001-visit001_3315-101_Sweet_02092025_20250902150849_11_fmri_MB3_ARC2_fMRI_1.5_mm_iso.nii.gz"
    ]
    
    # Output directory
    output_base_dir = "/Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python/qa_output_batch"
    os.makedirs(output_base_dir, exist_ok=True)
    
    print(f"🚀 Starting batch QA processing for {len(files_to_process)} files")
    print(f"Output directory: {output_base_dir}")
    
    successful_outputs = []
    failed_files = []
    
    # Process each file
    for filename in files_to_process:
        file_path = os.path.join(func_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            failed_files.append(filename)
            continue
        
        success, output_dir = run_memory_optimized_qa(file_path, output_base_dir)
        
        if success:
            successful_outputs.append(output_dir)
        else:
            failed_files.append(filename)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"BATCH PROCESSING SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {len(successful_outputs)}")
    print(f"❌ Failed: {len(failed_files)}")
    
    if successful_outputs:
        print(f"\nSuccessful outputs:")
        for output_dir in successful_outputs:
            print(f"  • {output_dir}")
    
    if failed_files:
        print(f"\nFailed files:")
        for failed_file in failed_files:
            print(f"  • {failed_file}")
    
    print(f"\nBatch processing complete!")
    
    return successful_outputs

if __name__ == "__main__":
    main()