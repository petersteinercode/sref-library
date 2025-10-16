#!/usr/bin/env python3
"""
Upload images to Vercel Blob Storage

This script uploads all images from static/images/ to Vercel Blob storage
and creates a mapping file for the Flask app to use.

Prerequisites:
1. Create a Vercel Blob store in your Vercel dashboard
2. Install Node.js and npm
3. Run: npm install @vercel/blob
4. Set up environment variables (BLOB_READ_WRITE_TOKEN)
"""

import os
import json
import subprocess
import glob
from pathlib import Path

def run_node_script(script_content, cwd=None):
    """Run a Node.js script and return the output."""
    try:
        result = subprocess.run(
            ['node', '-e', script_content],
            capture_output=True,
            text=True,
            cwd=cwd
        )
        if result.returncode != 0:
            print(f"Error running Node.js script: {result.stderr}")
            return None
        return result.stdout.strip()
    except FileNotFoundError:
        print("Node.js not found. Please install Node.js first.")
        return None

def upload_image_to_blob(image_path, blob_path):
    """Upload a single image to Vercel Blob."""
    script = f"""
const {{ put }} = require('@vercel/blob');
const fs = require('fs');

async function uploadImage() {{
    try {{
        const fileBuffer = fs.readFileSync('{image_path}');
        const blob = await put('{blob_path}', fileBuffer, {{
            access: 'public',
            contentType: 'image/jpeg'
        }});
        console.log(JSON.stringify(blob));
    }} catch (error) {{
        console.error('Upload error:', error.message);
        process.exit(1);
    }}
}}

uploadImage();
"""
    return run_node_script(script)

def upload_all_images():
    """Upload all images from static/images/ to Vercel Blob."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload...")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        blob_path = f"images/{filename}"
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        result = upload_image_to_blob(image_path, blob_path)
        if result:
            try:
                blob_info = json.loads(result)
                image_mapping[filename] = {
                    'url': blob_info['url'],
                    'pathname': blob_info['pathname'],
                    'size': blob_info['size']
                }
                print(f"  ✅ Uploaded: {blob_info['url']}")
            except json.JSONDecodeError:
                print(f"  ❌ Failed to parse response for {filename}")
        else:
            print(f"  ❌ Failed to upload {filename}")
    
    # Save mapping to file
    mapping_file = "blob_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✅ Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

def create_blob_upload_api():
    """Create a Vercel API route for uploading images."""
    api_dir = "api"
    os.makedirs(api_dir, exist_ok=True)
    
    upload_script = '''import { put } from '@vercel/blob';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return new Response('No file uploaded', { status: 400 });
    }

    const blob = await put(file.name, file, { 
      access: 'public',
      contentType: file.type 
    });
    
    return new Response(JSON.stringify(blob), { 
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(`Upload error: ${error.message}`, { status: 500 });
  }
}'''
    
    with open(os.path.join(api_dir, "upload.ts"), 'w') as f:
        f.write(upload_script)
    
    print("📄 Created API route: api/upload.ts")

if __name__ == "__main__":
    print("🚀 Vercel Blob Image Uploader")
    print("=" * 40)
    
    # Check if Node.js is available
    if not run_node_script("console.log('Node.js is working')"):
        print("❌ Node.js is required but not found.")
        print("Please install Node.js from https://nodejs.org/")
        exit(1)
    
    # Check if @vercel/blob is installed
    try:
        result = run_node_script("require('@vercel/blob'); console.log('SDK found')")
        if not result:
            print("❌ @vercel/blob package not found.")
            print("Please run: npm install @vercel/blob")
            exit(1)
    except:
        print("❌ @vercel/blob package not found.")
        print("Please run: npm install @vercel/blob")
        exit(1)
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        # Create API route
        create_blob_upload_api()
        
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Deploy your app to Vercel")
        print("2. The images will be served from Vercel Blob")
        print("3. Update your Flask app to use the blob URLs")

