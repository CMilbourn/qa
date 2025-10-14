# 🚀 fMRI QA Pipeline - Quick Reference

## ⚡ Most Common Commands

### 1. Complete Analysis + PowerPoint (One Step)
```bash
# Run QA analysis then create PowerPoint
python run_qa_simple.py --func_dir "/path/to/func/" --pattern "*fmri*"
python create_ppt_from_qa.py --qa_parent_dir "/path/to/func/" --func_dir "/path/to/func/" --output_name "Report.pptx"
```

### 2. PowerPoint from Existing QA Outputs
```bash
# If QA analysis already completed
python create_ppt_from_qa.py \
  --qa_parent_dir "/path/to/func/" \
  --func_dir "/path/to/func/" \
  --output_name "MyReport.pptx"
```

### 3. Enhanced PowerPoint with Full Metrics
```bash
# Most comprehensive report
python create_enhanced_ppt_from_qa.py \
  --qa_parent_dir "/path/to/func/" \
  --func_dir "/path/to/func/" \
  --output_name "DetailedReport.pptx"
```

## 📊 What You Get

### QA Metrics in PowerPoint
```
• TR (Repetition Time): 1.4s
• Ernst scaling factor: 0.8155  
• Image SNR (iSNR): 0.53
• Temporal SNR (tSNR): 8.01
• tSNR per unit time: 5.52
• Mean volume std: 1126.61
• Noise value used for iSNR: 1135.63
• Image data shape: 128 × 128 × 57 × 213 voxels
• Slice index: 12
```

### PowerPoint Contents
- **Title Slide**: Report overview
- **Summary Slide**: All datasets with metrics
- **Per-Dataset Slides**: Detailed metrics + categorized images
  - Mean Images (2 slides)
  - SNR Analysis (iSNR, tSNR maps)
  - Montage Views (slice galleries)
  - Noise Analysis (masking, noise volumes)
  - Time Series (temporal stability)

## 🔧 Setup (One Time)
```bash
# Install dependencies
pip install nibabel numpy scipy matplotlib scikit-learn python-pptx

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install nibabel numpy scipy matplotlib scikit-learn python-pptx
```

## 📁 File Requirements
- **NIfTI files**: `*.nii.gz` format
- **JSON sidecars**: Same basename as NIfTI (for TR detection)
- **Directory**: Any structure (BIDS or custom)

## 🎯 Example: Real Sub003 Data
```bash
# Your actual command from earlier:
cd /Users/cmilbourn/Documents/GitHub/qa/fMRI_report_python
source venv/bin/activate

python create_ppt_from_qa.py \
  --qa_parent_dir "/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/" \
  --func_dir "/Users/cmilbourn/Documents/Sweet_Data/Development_Data/sub003/sub003-visit001-ses001/func/" \
  --output_name "sub003_QA_Report.pptx"

# Output: 14MB PowerPoint with 64 QA images from 4 datasets
```

## ✅ Success Indicators
- **Processing**: `✅ QA analysis completed successfully!`
- **PowerPoint**: `✅ PowerPoint saved: /path/to/report.pptx`
- **File Size**: ~14MB for 4 datasets
- **Content**: 64 images (16 per dataset)

## 🔍 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| No files found | Check `--pattern` (try `"*bold*"` or `"*task*"`) |
| TR not detected | Verify JSON files exist with `RepetitionTime` |
| python-pptx error | `pip install python-pptx` |
| Images stretched | Use updated scripts (fixed in V2) |
| Large file sizes | Normal - QA generates many high-res images |

## 📊 Multi-TR Automatic Handling

The pipeline automatically:
- Detects TR from JSON files (1.4s, 2.0s, 2.026s, etc.)
- Applies appropriate Ernst scaling (0.5745 to 1.0)
- Calculates tSNR per unit time for comparison
- Includes all metrics in PowerPoint slides

## 🎯 Key Scripts Summary

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `run_qa_simple.py` | Batch QA analysis | Process multiple files |
| `create_ppt_from_qa.py` | Basic PowerPoint | Most common use case |
| `create_enhanced_ppt_from_qa.py` | Detailed PowerPoint | Comprehensive reports |
| `run_qa_with_ppt_V2_simple.py` | Complete pipeline | One-step analysis + PPT |

---
*Quick Reference v2.0 | October 2025*