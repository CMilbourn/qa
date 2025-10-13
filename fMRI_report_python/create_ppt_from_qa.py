#!/usr/bin/env python
"""
Create PowerPoint from existing QA output directories
Usage: python create_ppt_from_qa.py --qa_parent_dir /path/to/parent/ --output_name "report.pptx"
"""

import argparse
import os
import json
from datetime import datetime

# PowerPoint libraries
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    print("⚠️  python-pptx not installed.")

def get_tr_from_json(nifti_path):
    """Extract TR from corresponding JSON file"""
    try:
        json_path = nifti_path.replace('.nii.gz', '.json').replace('.nii', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                metadata = json.load(f)
                tr = metadata.get('RepetitionTime')
                if tr:
                    return float(tr)
    except Exception as e:
        print(f"Warning: Could not read TR from JSON: {e}")
    return None

def extract_metrics_from_qa_dirs(qa_output_dirs, func_dir=None):
    """Extract metrics from existing QA output directories"""
    metrics_list = []
    
    for qa_dir in qa_output_dirs:
        if not os.path.exists(qa_dir):
            continue
            
        # Extract filename from directory name
        dirname = os.path.basename(qa_dir)
        if dirname.startswith('qa_output_'):
            filename = dirname[10:]  # Remove 'qa_output_' prefix
        else:
            filename = dirname
            
        # Try to get TR from func directory
        tr_value = None
        if func_dir:
            for ext in ['.nii.gz', '.nii']:
                nifti_file = os.path.join(func_dir, filename + ext)
                if os.path.exists(nifti_file):
                    tr_value = get_tr_from_json(nifti_file)
                    break
        
        metrics = {
            'filename': filename,
            'tr': tr_value if tr_value else 'Unknown',
            'qa_dir': qa_dir
        }
        
        metrics_list.append(metrics)
    
    return metrics_list

def create_qa_powerpoint(qa_output_dirs, presentation_path, summary_data):
    """Create a PowerPoint presentation with QA results"""
    if not PPTX_AVAILABLE:
        print("❌ Cannot create PowerPoint - python-pptx not installed")
        return False
    
    print("🎨 Creating PowerPoint presentation...")
    
    # Create presentation
    prs = Presentation()
    
    # Title slide
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = "fMRI Quality Assessment Report"
    subtitle.text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{len(qa_output_dirs)} datasets analyzed"
    
    # Summary slide
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "QA Summary"
    
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.clear()
    
    p = tf.paragraphs[0]
    p.text = "Dataset Summary:"
    p.font.bold = True
    p.font.size = Pt(16)
    
    for i, data in enumerate(summary_data):
        p = tf.add_paragraph()
        p.text = f"\n{i+1}. {data['filename']}"
        p.font.size = Pt(12)
        p.font.bold = True
        
        p = tf.add_paragraph()
        p.text = f"   • TR: {data['tr']}s"
        p.font.size = Pt(10)
        
        qa_dir = data['qa_dir']
        if os.path.exists(qa_dir):
            image_files = [f for f in os.listdir(qa_dir) if f.endswith('.png')]
            p = tf.add_paragraph()
            p.text = f"   • {len(image_files)} QA images available"
            p.font.size = Pt(10)
    
    # Create slides for each dataset
    for i, (qa_dir, data) in enumerate(zip(qa_output_dirs, summary_data)):
        
        if not os.path.exists(qa_dir):
            continue
            
        # Dataset overview slide
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        title.text = f"Dataset {i+1}: {data['filename']}"
        
        content = slide.placeholders[1]
        tf = content.text_frame
        tf.clear()
        
        p = tf.paragraphs[0]
        p.text = f"File: {data['filename']}"
        p.font.size = Pt(14)
        p.font.bold = True
        
        # List available images
        image_files = [f for f in os.listdir(qa_dir) if f.endswith('.png')]
        info_text = f"\nDataset Information:\n• TR: {data['tr']}s\n• QA Directory: {os.path.basename(qa_dir)}\n\nAvailable Images ({len(image_files)}):\n"
        
        for img_file in sorted(image_files):
            info_text += f"• {img_file}\n"
        
        p = tf.add_paragraph()
        p.text = info_text
        p.font.size = Pt(12)
        
        # Group and display images
        image_groups = {
            'Mean Images': [f for f in image_files if 'mean' in f.lower()],
            'SNR Analysis': [f for f in image_files if any(x in f.lower() for x in ['isnr', 'tsnr', 'snr'])],
            'Montage Views': [f for f in image_files if 'montage' in f.lower()],
            'Noise Analysis': [f for f in image_files if 'noise' in f.lower()],
            'Time Series': [f for f in image_files if any(x in f.lower() for x in ['ts_', 'timeseries'])],
            'Other': [f for f in image_files if not any(keyword in f.lower() for keyword in ['mean', 'snr', 'montage', 'noise', 'ts_', 'timeseries'])]
        }
        
        for category, images in image_groups.items():
            if not images:
                continue
                
            # Create slide for this category
            slide_layout = prs.slide_layouts[6]  # Blank layout
            slide = prs.slides.add_slide(slide_layout)
            
            # Add title
            title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.8))
            title_frame = title_shape.text_frame
            title_para = title_frame.paragraphs[0]
            title_para.text = f"Dataset {i+1}: {category}"
            title_para.font.size = Pt(18)
            title_para.font.bold = True
            title_para.alignment = PP_ALIGN.CENTER
            
            # Add images (up to 4 per slide)
            y_pos = Inches(1.0)
            for j, img_file in enumerate(images[:4]):
                img_path = os.path.join(qa_dir, img_file)
                if os.path.exists(img_path):
                    try:
                        # Position images in a 2x2 grid with preserved aspect ratio
                        left = Inches(0.5 + (j % 2) * 4.75)
                        if j >= 2:
                            y_pos = Inches(4.0)
                        
                        # Add image with preserved aspect ratio (no width/height specified)
                        pic = slide.shapes.add_picture(img_path, left, y_pos)
                        
                        # Scale down if too large, maintaining aspect ratio
                        max_width = Inches(4.5)
                        max_height = Inches(3)
                        
                        if pic.width > max_width:
                            ratio = max_width / pic.width
                            pic.width = max_width
                            pic.height = int(pic.height * ratio)
                        
                        if pic.height > max_height:
                            ratio = max_height / pic.height
                            pic.height = max_height
                            pic.width = int(pic.width * ratio)
                        
                        # Add caption
                        caption_shape = slide.shapes.add_textbox(left, y_pos + Inches(3), Inches(4), Inches(0.5))
                        caption_frame = caption_shape.text_frame
                        caption_para = caption_frame.paragraphs[0]
                        caption_para.text = img_file.replace('.png', '').replace('_', ' ').title()
                        caption_para.font.size = Pt(9)
                        caption_para.alignment = PP_ALIGN.CENTER
                        
                    except Exception as e:
                        print(f"⚠️  Could not add image {img_file}: {e}")
    
    # Save presentation
    try:
        prs.save(presentation_path)
        print(f"✅ PowerPoint saved: {presentation_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving PowerPoint: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create PowerPoint from existing QA output directories')
    parser.add_argument('--qa_parent_dir', required=True, help='Parent directory containing qa_output_* folders')
    parser.add_argument('--func_dir', help='Optional func directory to extract TR values')
    parser.add_argument('--output_name', default='QA_Report.pptx', help='PowerPoint filename')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.qa_parent_dir):
        print(f"❌ Directory does not exist: {args.qa_parent_dir}")
        return 1
    
    # Find QA output directories
    qa_dirs = []
    for item in os.listdir(args.qa_parent_dir):
        if item.startswith('qa_output_') and os.path.isdir(os.path.join(args.qa_parent_dir, item)):
            qa_dirs.append(os.path.join(args.qa_parent_dir, item))
    
    if not qa_dirs:
        print(f"❌ No qa_output_* directories found in {args.qa_parent_dir}")
        return 1
    
    print(f"📁 Found {len(qa_dirs)} QA output directories:")
    for qa_dir in qa_dirs:
        print(f"   • {os.path.basename(qa_dir)}")
    
    # Extract metrics
    summary_data = extract_metrics_from_qa_dirs(qa_dirs, args.func_dir)
    
    # Create PowerPoint
    ppt_path = os.path.join(args.qa_parent_dir, args.output_name)
    success = create_qa_powerpoint(qa_dirs, ppt_path, summary_data)
    
    if success:
        print(f"🎉 PowerPoint report created successfully!")
        print(f"📄 File: {ppt_path}")
    else:
        print("❌ Failed to create PowerPoint report")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())