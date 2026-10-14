import sys
sys.path.append('/Users/cmilbourn/Documents/GitHub/qa/')
from fMRI_report_python.qa_run_nophase_V12_MASK_40dyn_V8_combi import find_echo_files, load_data, get_te_from_json
import os

# Test directory
test_dir = '/Users/cmilbourn/Documents/Sweet_Data/Development_Data_Phase3/nifti/20260620_phantomrun_5/Run1/'

# Test pattern
base_pattern = 'phantom_A_Sweet_20260611_P3_dev_20260619121446_2_A_Default_HyperMEPI_multiphase_FA68_MB3'

print(f"Looking for echo files in: {test_dir}")
print(f"Base pattern: {base_pattern}")

echo_files = find_echo_files(test_dir, base_pattern)

if echo_files:
    print("\nFound echo files:")
    for key, path in echo_files.items():
        te = get_te_from_json(path)
        print(f"  {key}: {os.path.basename(path)}")
        print(f"    TE: {te}")
else:
    print("No echo files found!")

# List files in directory
print("\nFiles in directory:")
for f in sorted(os.listdir(test_dir)):
    if f.endswith(('.nii', '.nii.gz')):
        print(f"  {f}")
