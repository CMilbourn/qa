#!/bin/bash
#
# Preprocessing script for tSNR_check_30dyn dataset
# This script processes multiple fMRI datasets with QA analysis
#
# Created: 28 November 2025
#format_data2run.sh
# Base paths
SCRIPT_DIR="/Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python"
INPUT_DIR="/Users/cmilbourn/Documents/tSNR_check_30dyn/Data2run/rawish"
OUTPUT_BASE="/Users/cmilbourn/Documents/tSNR_check_30dyn/Data2run/preprocessed"
#QA_SCRIPT="${SCRIPT_DIR}/qa_run_nophase_V9_multisubj_MASK_30dyn.py"
#METADATA_CSV="/Users/cmilbourn/Documents/tSNR_check_30dyn/Data2run/dataset_info_filled.csv"

# Create output directory
#mkdir -p "${OUTPUT_BASE}"

# Array of input files
declare -a FILES=(
    "${INPUT_DIR}/sub001-visit001_3315-101_Sweet_02092025_20250902150849_4_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit001_3315-101_Sweet_02092025_20250902150849_7_fmri_MB3_ARC2_fMRI_2mm_1.5_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit001_3315-101_Sweet_02092025_20250902150849_11_fmri_MB3_ARC2_fMRI_1.5_mm_iso_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit001-ses001-task-rest-asl_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit001-ses001-task-rest-bold_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit002-ses001-task-rest-asl-pre_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit002-ses001-task-rest-bold-pre_nodummies.nii.gz"
    "${INPUT_DIR}/sub001-visit003-ses001-task-rest-bold-pre_nodummies.nii.gz"
    "${INPUT_DIR}/sub003-visit001-ses001-Sweet_20250909_phase3_de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105_nodummies.nii.gz"
    "${INPUT_DIR}/sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105_nodummies.nii.gz"
    "${INPUT_DIR}/sub003-visit001-ses001-Sweet_20250909_phase3_de-8-fmri_MB3_ARC2_fMRI_3mm-20251009110105_nodummies.nii.gz"
    "${INPUT_DIR}/sub003-visit001-ses001-Sweet_20250909_phase3_de-9-fmri_MB2_ARC2_fMRI_2mm_pre-20251009110105_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_3_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_4_fmri_MB2_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_5_TR2.5_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_6_TR2.5_fmri_MB2_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_7_PAPER_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_8_2.5mmisofmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_9_2mmiso_TR2_fmri_MB3_ARC2_fMRI_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_10_2mmiso_TR2_fmri_MB2_ARC2_fMRI_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_11_MB1_TASK_fMRI_TR2000_1_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_12_tr1.4_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_13_tr2.5_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/Sub004-visit001-ses001_A_Sweet_20250604_dev_20251125114539_14_tr2_fmri_MB3_ARC2_fMRI_2mm_nodummies.nii.gz"
    "${INPUT_DIR}/sub14_task-hyper_run-1_bold_nodummies.nii.gz"
    "${INPUT_DIR}/sub14_task-normo_asl_nodummies.nii.gz"
)

# Array of files that are already 30 dynamics (skip fslroi, only run BET)
declare -a FILES_ALREADY_30DYN=(
    "${INPUT_DIR}/TR1_MB3_single_echo_15_1.nii.gz"
    "${INPUT_DIR}/TR1p25_MB3_S1p8_10_1_ws_map.nii.gz"
    "${INPUT_DIR}/TR1p25_MB2_S1p8_11_1_ws_map.nii.gz"
)


echo "========================================================================"
echo "fMRI QA Preprocessing - tSNR Check 30 Dynamics"
echo "========================================================================"
echo "Input directory: ${INPUT_DIR}"
echo "Output directory: ${OUTPUT_BASE}"
echo "Total files to process: ${#FILES[@]}"
echo "Files already at 30 dynamics: ${#FILES_ALREADY_30DYN[@]}"
echo "========================================================================"
echo ""

# Check if files exist
echo "Checking file existence..."
missing_count=0
for file in "${FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "  WARNING: File not found: $file"
        ((missing_count++))
    fi
done

for file in "${FILES_ALREADY_30DYN[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "  WARNING: File not found: $file"
        ((missing_count++))
    fi
done

if [[ $missing_count -gt 0 ]]; then
    echo ""
    echo "ERROR: $missing_count files are missing!"
    echo "Please check the input directory and file names."
    exit 1
fi

echo "All files found!"
echo ""

# Process each file - extract first 30 volumes using fslroi
echo "========================================================================"
echo "Processing files: Extracting first 30 volumes..."
echo "========================================================================"
echo ""

success_count=0
fail_count=0
bet_success_count=0
bet_fail_count=0

for i in "${!FILES[@]}"; do
    input_file="${FILES[$i]}"
    base_name=$(basename "$input_file" .nii.gz)
    output_file="${OUTPUT_BASE}/${base_name}_30dyn.nii.gz"
    
    echo "[$((i+1))/${#FILES[@]}] Processing: $(basename "$input_file")"
    
    # Check number of volumes in input file
    nvols=$(fslnvols "$input_file" 2>/dev/null)
    if [[ $? -ne 0 ]]; then
        echo "  ERROR: Could not read number of volumes from $input_file"
        ((fail_count++))
        continue
    fi
    
    echo "  Input volumes: $nvols"
    
    # Extract first 30 volumes (0-indexed, so 0 to 29)
    if [[ $nvols -ge 30 ]]; then
        fslroi "$input_file" "$output_file" 0 30
        if [[ $? -eq 0 ]]; then
            echo "  SUCCESS: Created $output_file (30 volumes)"
            ((success_count++))
        else
            echo "  ERROR: fslroi failed for $input_file"
            ((fail_count++))
            continue
        fi
    else
        echo "  WARNING: File has only $nvols volumes (< 30). Copying all volumes..."
        cp "$input_file" "$output_file"
        if [[ $? -eq 0 ]]; then
            echo "  SUCCESS: Copied $output_file ($nvols volumes)"
            ((success_count++))
        else
            echo "  ERROR: Copy failed for $input_file"
            ((fail_count++))
            continue
        fi
    fi
    
    # Run BET brain extraction on the output file
    bet_output_stem="${OUTPUT_BASE}/${base_name}_30dyn"
    echo "  Running BET brain extraction..."
    bet "$output_file" "${bet_output_stem}_brain" -f 0.5 -m
    if [[ $? -eq 0 ]]; then
        echo "  SUCCESS: Brain extraction complete"
        echo "    - Brain: ${bet_output_stem}_brain.nii.gz"
        echo "    - Mask: ${bet_output_stem}_brain_mask.nii.gz"
        ((bet_success_count++))
    else
        echo "  ERROR: BET failed for $output_file"
        ((bet_fail_count++))
    fi
    
    echo ""
done

# Process files that are already 30 dynamics (only run BET)
echo "========================================================================"
echo "Processing files already at 30 dynamics (BET only)..."
echo "========================================================================"
echo ""

for i in "${!FILES_ALREADY_30DYN[@]}"; do
    input_file="${FILES_ALREADY_30DYN[$i]}"
    base_name=$(basename "$input_file" .nii.gz)
    output_file="${OUTPUT_BASE}/${base_name}.nii.gz"
    
    echo "[$((i+1))/${#FILES_ALREADY_30DYN[@]}] Processing: $(basename "$input_file")"
    
    # Copy file to output directory
    cp "$input_file" "$output_file"
    if [[ $? -ne 0 ]]; then
        echo "  ERROR: Copy failed for $input_file"
        ((fail_count++))
        continue
    fi
    echo "  SUCCESS: Copied to output directory"
    ((success_count++))
    
    # Run BET brain extraction
    bet_output_stem="${OUTPUT_BASE}/${base_name}"
    echo "  Running BET brain extraction..."
    bet "$output_file" "${bet_output_stem}_brain" -f 0.5 -m
    if [[ $? -eq 0 ]]; then
        echo "  SUCCESS: Brain extraction complete"
        echo "    - Brain: ${bet_output_stem}_brain.nii.gz"
        echo "    - Mask: ${bet_output_stem}_brain_mask.nii.gz"
        ((bet_success_count++))
    else
        echo "  ERROR: BET failed for $output_file"
        ((bet_fail_count++))
    fi
    
    echo ""
done

echo "========================================================================"
echo "Processing Summary"
echo "========================================================================"
echo "Total files processed: $((${#FILES[@]} + ${#FILES_ALREADY_30DYN[@]}))"
echo ""
echo "Volume extraction (fslroi):"
echo "  Successful: $success_count"
echo "  Failed: $fail_count"
echo ""
echo "Brain extraction (BET):"
echo "  Successful: $bet_success_count"
echo "  Failed: $bet_fail_count"
echo ""
echo "Output directory: ${OUTPUT_BASE}"
echo "========================================================================"

if [[ $fail_count -gt 0 ]] || [[ $bet_fail_count -gt 0 ]]; then
    exit 1
else
    exit 0
fi





