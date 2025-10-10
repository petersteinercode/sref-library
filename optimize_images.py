#!/usr/bin/env python3
"""
Image optimization script for output_test folder
Dramatically reduces image file sizes while maintaining good quality
"""

import os
import sys
from PIL import Image
import argparse
from pathlib import Path

def optimize_image(input_path, output_path, max_width=400, quality=35, format='JPEG'):
    """
    Optimize a single image file
    
    Args:
        input_path: Path to input image
        output_path: Path to output image
        max_width: Maximum width in pixels (height will be scaled proportionally)
        quality: JPEG quality (1-100, higher = better quality, larger file)
        format: Output format ('JPEG' or 'PNG')
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for JPEG output)
            if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif format == 'JPEG':
                img = img.convert('RGB')
            
            # Calculate new dimensions
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with optimization
            save_kwargs = {
                'optimize': True,
                'progressive': True if format == 'JPEG' else False
            }
            
            if format == 'JPEG':
                save_kwargs['quality'] = quality
            elif format == 'PNG':
                save_kwargs['compress_level'] = 9
            
            img.save(output_path, format=format, **save_kwargs)
            
            return True, None
            
    except Exception as e:
        return False, str(e)

def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def main():
    parser = argparse.ArgumentParser(description='Optimize images in output_test folder')
    parser.add_argument('--input-dir', default='output_test', help='Input directory (default: output_test)')
    parser.add_argument('--output-dir', default='output_test_optimized', help='Output directory (default: output_test_optimized)')
    parser.add_argument('--max-width', type=int, default=400, help='Maximum width in pixels (default: 400)')
    parser.add_argument('--quality', type=int, default=35, help='JPEG quality 1-100 (default: 35)')
    parser.add_argument('--format', choices=['JPEG', 'PNG'], default='JPEG', help='Output format (default: JPEG)')
    parser.add_argument('--test', action='store_true', help='Test on first 5 images only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually doing it')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)
    
    # Get all JPG files
    jpg_files = list(input_dir.glob('*.jpg'))
    if not jpg_files:
        print(f"No JPG files found in '{input_dir}'")
        sys.exit(1)
    
    # Limit to test files if requested
    if args.test:
        jpg_files = jpg_files[:5]
        print(f"TEST MODE: Processing only {len(jpg_files)} files")
    
    print(f"Found {len(jpg_files)} JPG files to process")
    print(f"Settings: max_width={args.max_width}, quality={args.quality}, format={args.format}")
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        for jpg_file in jpg_files:
            print(f"Would process: {jpg_file.name}")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Calculate total original size
    total_original_size = sum(get_file_size_mb(f) for f in jpg_files)
    print(f"Total original size: {total_original_size:.1f} MB")
    
    # Process files
    successful = 0
    failed = 0
    total_new_size = 0
    
    for i, jpg_file in enumerate(jpg_files, 1):
        # Determine output filename
        if args.format == 'JPEG':
            output_file = output_dir / (jpg_file.stem + '.jpg')
        else:
            output_file = output_dir / jpg_file.name
        
        print(f"[{i}/{len(jpg_files)}] Processing {jpg_file.name}...", end=' ')
        
        success, error = optimize_image(jpg_file, output_file, args.max_width, args.quality, args.format)
        
        if success:
            original_size = get_file_size_mb(jpg_file)
            new_size = get_file_size_mb(output_file)
            reduction = (1 - new_size / original_size) * 100
            total_new_size += new_size
            
            print(f"✓ {original_size:.1f}MB → {new_size:.1f}MB ({reduction:.1f}% reduction)")
            successful += 1
        else:
            print(f"✗ Error: {error}")
            failed += 1
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Original total size: {total_original_size:.1f} MB")
    print(f"New total size: {total_new_size:.1f} MB")
    if total_original_size > 0:
        total_reduction = (1 - total_new_size / total_original_size) * 100
        print(f"Total size reduction: {total_reduction:.1f}%")
        print(f"Space saved: {total_original_size - total_new_size:.1f} MB")

if __name__ == '__main__':
    main()
