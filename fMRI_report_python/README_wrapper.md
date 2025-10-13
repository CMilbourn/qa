# fMRI QA Analysis Wrapper

This wrapper script allows you to easily run fMRI QA analysis on multiple subjects and visits without manually editing the main script.

## Usage

### Single Subject/Visit
```bash
# Basic usage
python run_qa_batch.py --subject sub001 --visit visit001 --session ses001

# With custom base path
python run_qa_batch.py --base_path /path/to/your/data --subject sub002 --visit visit002

# Different task
python run_qa_batch.py --subject sub001 --visit visit001 --task motor

# Different file extension
python run_qa_batch.py --subject sub001 --visit visit001 --extension .nii
```

### Multiple Subjects from Config File
```bash
python run_qa_batch.py --config example_config.txt
```

### Command Line Options
- `--base_path`: Base path to your BIDS dataset (default: current path in script)
- `--subject`: Subject ID (e.g., sub001)
- `--visit`: Visit ID (e.g., visit001) 
- `--session`: Session ID (e.g., ses001) - optional
- `--task`: Task name (default: rest)
- `--extension`: File extension (default: .nii.gz)
- `--config`: Configuration file for batch processing

## Configuration File Format

Create a text file with the following format:

```ini
[DEFAULT]
base_path = /path/to/your/data
extension = .nii.gz
task = rest

[sub001]
visit = visit001
session = ses001

[sub002]
visit = visit002
session = ses002
task = motor  # Override default task
```

## Output

For each processed file, the script creates a `qa_output_[filename]` directory containing:
- NIfTI files: iSNR and tSNR maps
- PNG plots: Various quality assessment visualizations
- Console output with key metrics

## File Structure Expected

The script expects BIDS-formatted data:
```
base_path/
├── sub001/
│   └── sub001-visit001/
│       └── func/
│           ├── sub001-visit001-ses001-task-rest-bold.nii.gz
│           └── [optional mask file with 'mask' in filename]
└── sub002/
    └── sub002-visit002/
        └── func/
            └── sub002-visit002-ses002-task-rest-bold.nii.gz
```

## Examples

1. **Process one subject:**
   ```bash
   python run_qa_batch.py --subject sub001 --visit visit001 --session ses001
   ```

2. **Process multiple subjects from config:**
   ```bash
   python run_qa_batch.py --config my_subjects.txt
   ```

3. **Different data location:**
   ```bash
   python run_qa_batch.py --base_path /mnt/data --subject sub001 --visit visit001
   ```

## Original Script

The original `qa_run_nophase.py` can still be used directly with manual path editing, or you can call its functions programmatically from other scripts.