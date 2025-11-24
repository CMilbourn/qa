#!/bin/bash
# run BET on tSNR datasets
# 20251121 Colette Milbourn

# Array of input files
files=(
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_11_fmri_MB3_ARC2_fMRI_1.5_mm_iso.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_7_fmri_MB3_ARC2_fMRI_2mm_1.5.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/func/sub001-visit001_3315-101_Sweet_02092025_20250902150849_4_fmri_MB3_ARC2_fMRI_2mm.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit002/func/sub001-visit002-ses001-task-rest-bold-pre.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-9-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-8-fmri_MB3_ARC2_fMRI_3mm-20251009110105.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/sub003-visit001-ses001-Sweet_20250909_phase3_de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1_MB3_single_echo_15_1.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p5_MB2_doublecho_13_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p5_MB3_doublecho_14_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB2_doublecho_9_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB2_S1p8_11_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB3_doublecho_8_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR1p25_MB3_S1p8_10_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/BGI_Data/BGI_tSNR_fromSally/fMRI-test/nifti_converted/TR2_MB3_doublecho_2_1_ws_map.nii.gz"
"/Users/cmilbourn/Documents/PhD_GE_Data/sub14_task-normo_asl.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit002/perf/sub001-visit002-ses001-task-rest-asl-pre.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit001/perf/sub001-visit001-ses001-task-rest-asl.nii.gz"
"/Users/cmilbourn/Documents/PhD_GE_Data/sub14_task-hyper_run-1_bold.nii.gz"
"/Users/cmilbourn/Documents/Sweet_Data/Development_Data/Sweet_Data_BIDS_Dev/sub001/sub001-visit003/func/sub001-visit003-ses001-task-rest-bold-pre.nii.gz"
)

echo "Running BET on ${#files[@]} datasets..."
echo ""

# Loop through each file
for i in "${!files[@]}"; do
    input_file="${files[$i]}"
    
    # Check if file exists
    if [ ! -f "$input_file" ]; then
        echo "[$((i+1))/${#files[@]}] SKIPPING - File not found: $input_file"
        continue
    fi
    
    # Create output filename by inserting _brain_mask before .nii.gz
    output_file="${input_file%.nii.gz}_brain_mask.nii.gz"
    
    echo "[$((i+1))/${#files[@]}] Processing: $(basename "$input_file")"
    echo "  Input:  $input_file"
    echo "  Output: $output_file"
    
    # Run BET
    ${FSLDIR}/bin/bet "$input_file" "$output_file" -f 0.5 -m
    chmod 755 "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "  ✓ SUCCESS"
    else
        echo "  ✗ FAILED"
    fi
    echo ""
done

echo "All datasets processed!"
