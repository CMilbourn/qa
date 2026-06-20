#!/bin/bash
# Extract EchoTime and FlipAngle from JSON sidecars for a list of NIfTI files

# List of NIfTI files
nifti_files=(
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

# Print header
echo "File,EchoTime,FlipAngle"

for nifti in "${nifti_files[@]}"; do
    json_file="${nifti%.nii.gz}.json"
    if [ -f "$json_file" ]; then
        echo_time=$(grep -o '"EchoTime"[[:space:]]*:[[:space:]]*[0-9.]*' "$json_file" | grep -o '[0-9.][0-9.]*')
        flip_angle=$(grep -o '"FlipAngle"[[:space:]]*:[[:space:]]*[0-9.]*' "$json_file" | grep -o '[0-9.][0-9.]*')
        echo "$nifti,$echo_time,$flip_angle"
    else
        echo "$nifti,,"  # JSON not found
    fi
done
