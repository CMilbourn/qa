# fMRI QA Pipeline Documentation

## 📋 Complete Pipeline Guide

This document provides comprehensive instructions for using the fMRI Quality Assessment pipeline with PowerPoint reporting capabilities.

## 🚀 Quick Reference

### Most Common Usage

**For single analysis with PowerPoint:**
```bash
python create_ppt_from_qa.py \
  --qa_parent_dir "/path/to/func/" \
  --func_dir "/path/to/func/" \
  --output_name "MyReport.pptx"
```

**For batch processing multiple TRs:**
```bash
python run_qa_simple.py \
  --func_dir "/path/to/func/" \
  --pattern "*fmri*"
```

## 📊 What the Pipeline Does

### Automatic TR Detection
- Reads `RepetitionTime` from BIDS JSON sidecar files
- Supports any TR value (tested: 1.4s, 2.0s, 2.026s)
- Applies appropriate Ernst angle scaling factors

### Ernst Scaling Factors
```
TR ≤ 0.7s  → 0.5745 (sin(35°))
TR ≤ 1.0s  → 0.7071 (sin(45°))  
TR ≤ 1.5s  → 0.8155 (sin(54.7°))
TR > 1.5s  → 1.0000 (sin(90°))
```

### QA Metrics Generated
- **Image SNR (iSNR)**: Signal-to-noise ratio using noise scan
- **Temporal SNR (tSNR)**: Time series stability
- **tSNR per unit time**: TR-normalized for protocol comparison
- **Noise analysis**: Brain masking and noise characterization
- **Data shape**: Voxel dimensions and time points
- **Slice information**: Central slice indices
- **Ernst scaling**: Applied scaling factors

## 🛠️ Scripts Overview

### PowerPoint Generation (Recommended)

#### `create_ppt_from_qa.py` ⭐️ **Most Used**
- Creates PowerPoint from existing QA outputs
- **Fixed aspect ratios** - images no longer stretched
- **Comprehensive metrics** from command line included
- **Organized slides** by image category

**Usage:**
```bash
python create_ppt_from_qa.py \
  --qa_parent_dir "/Users/data/sub003/func/" \
  --func_dir "/Users/data/sub003/func/" \
  --output_name "sub003_QA_Report.pptx"
```

#### `create_enhanced_ppt_from_qa.py`
- Enhanced version with NIFTI analysis
- More detailed metrics extraction
- Comprehensive data characteristics

### QA Analysis Scripts

#### `run_qa_simple.py` ⭐️ **Batch Processing**
- Processes multiple files with different TRs
- Automatic TR detection and Ernst scaling
- Progress tracking and error handling

**Usage:**
```bash
python run_qa_simple.py \
  --func_dir "/Users/data/sub003/func/" \
  --pattern "*fmri*"
```

#### `qa_with_tr_detection.py`
- Single file analysis with TR auto-detection
- Enhanced version of original QA script

#### `run_qa_batch.py`
- BIDS-compatible batch processor
- Subject/visit/session structure

## 📈 PowerPoint Report Contents

### Report Structure
1. **Title Slide** - Overview with timestamp
2. **Summary Slide** - All datasets with key metrics
3. **Per-Dataset Slides**:
   - Detailed metrics overview
   - Mean Images
   - SNR Analysis (iSNR, tSNR maps)
   - Montage Views
   - Noise Analysis
   - Time Series Analysis

### Metrics Displayed
```
QA Metrics Summary:
• TR (Repetition Time): 1.4s
• Ernst scaling factor: 0.8155
• Image data shape: 128 × 128 × 57 × 213 voxels
• Image SNR (iSNR): 0.53
• Temporal SNR (tSNR): 8.01
• tSNR per unit time: 5.52
• Mean volume std: 1126.61
• Noise value used for iSNR: 1135.63
• Slice index: 12
```

## 🔄 Typical Workflow

### Step 1: Run QA Analysis
```bash
# Process all fMRI files in directory
cd /path/to/qa/pipeline
source venv/bin/activate

python run_qa_simple.py \
  --func_dir "/Users/data/sub003/func/" \
  --pattern "*fmri*"
```

**Output:** Creates `qa_output_*` directories for each file

### Step 2: Generate PowerPoint Report
```bash
# Create comprehensive PowerPoint report
python create_ppt_from_qa.py \
  --qa_parent_dir "/Users/data/sub003/func/" \
  --func_dir "/Users/data/sub003/func/" \
  --output_name "sub003_QA_Report.pptx"
```

**Output:** Professional PowerPoint with all QA images and metrics

## 📁 File Structure Examples

### Input Files
```
func/
├── sub003-visit001-ses001-Sweet_20250909_phase3_de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.nii.gz
├── sub003-visit001-ses001-Sweet_20250909_phase3_de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105.json
├── sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105.nii.gz
├── sub003-visit001-ses001-Sweet_20250909_phase3_de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105.json
└── ...
```

### Generated Outputs
```
func/
├── qa_output_sub003-...-de-2-fmri_MB3_ARC2_fMRI_2mm_pre-20251009110105/
│   ├── Mean_image.png
│   ├── mean_montage.png
│   ├── iSNR_sag.png, iSNR_cor.png
│   ├── tSNR_sag.png, tSNR_cor.png
│   ├── isnr_montage.png, tSNR_montage.png
│   ├── masked_noise.png
│   ├── TS_images.png
│   ├── tSNR_raw.png, tSNR_per_unit_time.png
│   ├── SSN.png
│   └── *.nii.gz files (isnr, tsnr, etc.)
├── qa_output_sub003-...-de-5-fmri_MB3_ARC2_fMRI_2mm_longerTR-20251009110105/
│   └── [same structure]
└── sub003_QA_Report.pptx  (14MB with all images)
```

## ✨ Key Features

### Automatic TR Handling
- **Multi-TR Support**: Processes files with different TRs automatically
- **JSON Integration**: Reads TR from BIDS sidecar files
- **Ernst Scaling**: Applies appropriate scaling per TR
- **Unit Time Normalization**: Enables fair protocol comparison

### PowerPoint Enhancements
- **Preserved Aspect Ratios**: Images maintain original proportions
- **Comprehensive Metrics**: All command-line output included
- **Professional Layout**: Organized by analysis category
- **Batch Reporting**: Multiple datasets in single presentation

### Robust Processing
- **Error Handling**: Continues processing if individual files fail
- **Progress Tracking**: Real-time status updates
- **Flexible Patterns**: Customizable file matching
- **Output Management**: Organized directory structure

## 🔧 Installation & Setup

### Prerequisites
```bash
pip install nibabel numpy scipy matplotlib scikit-learn python-pptx
```

### Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install nibabel numpy scipy matplotlib scikit-learn python-pptx
```

## 📊 Quality Assessment Interpretation

### Good QA Values
- **iSNR**: > 0.3 (higher is better)
- **tSNR**: > 50 in gray matter (higher is better)
- **Mean volume std**: < 2000 (lower variability is better)
- **Noise values**: Consistent across similar protocols

### TR-Specific Considerations
- **Short TR (< 1.0s)**: Lower absolute tSNR expected
- **Long TR (> 2.0s)**: Higher absolute tSNR but consider acquisition time
- **tSNR per unit time**: Use for fair comparison across TRs

## 🚀 Advanced Usage

### Custom Patterns
```bash
# Different file naming patterns
--pattern "*bold*"      # For BOLD files
--pattern "*task*"      # For task files  
--pattern "*rest*"      # For resting state
--pattern "*run-01*"    # For specific runs
```

### BIDS Processing
```bash
# Batch configuration file
cat > batch_config.txt << EOF
sub001,visit001,ses001
sub002,visit001,ses001
sub003,visit001,ses001
EOF

python run_qa_batch.py --config batch_config.txt
```

### Enhanced Reporting
```bash
# Most comprehensive report
python create_enhanced_ppt_from_qa.py \
  --qa_parent_dir "/path/to/func/" \
  --func_dir "/path/to/func/" \
  --output_name "Detailed_QA_Report.pptx"
```

## 🔍 Troubleshooting

### Common Issues

**"No files found matching pattern"**
```bash
# Check available files
ls /path/to/func/*.nii.gz
# Adjust pattern as needed
```

**"TR not found in JSON"**
```bash
# Verify JSON files exist
ls /path/to/func/*.json
# Check JSON content
grep RepetitionTime /path/to/func/*.json
```

**"python-pptx not installed"**
```bash
pip install python-pptx
```

### Expected File Sizes
- **QA Output**: ~50-100MB per dataset (16 PNG images + NIfTI files)
- **PowerPoint**: ~14MB for 4 datasets (64 images total)
- **Processing Time**: ~30-60 seconds per dataset

---

## 📞 Quick Help

**Most Common Command:**
```bash
# Complete workflow for directory with multiple TR files
python run_qa_simple.py --func_dir "/path/to/func/" --pattern "*fmri*"
python create_ppt_from_qa.py --qa_parent_dir "/path/to/func/" --func_dir "/path/to/func/" --output_name "Report.pptx"
```

**File Requirements:**
- NIfTI files (`.nii.gz`)
- JSON sidecar files (same basename)
- Optional mask files (auto-detected)

**Key Output:**
- Professional PowerPoint report
- Comprehensive QA metrics
- Multi-TR protocol comparison
- Fixed aspect ratio images

*Pipeline Version 2.0 | October 2025*