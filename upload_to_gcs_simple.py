#!/usr/bin/env python3
"""
Upload images to Google Cloud Storage using gcloud authentication

This script uploads all images from static/images/ to your GCS bucket
and creates a mapping file for the Flask app to use.

Uses your existing gcloud authentication - no additional setup needed!
"""

import os
import json
import glob
from google.cloud import storage

# Your bucket name (created above)
BUCKET_NAME = "sref-library-images-1760105562"

def upload_all_images():
    """Upload all images from static/images/ to GCS."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Set up GCS client (uses your gcloud authentication automatically)
    try:
        client = storage.Client()
        print(f"✅ Connected to Google Cloud Storage")
        print(f"📁 Using bucket: {BUCKET_NAME}")
    except Exception as e:
        print(f"❌ Error connecting to GCS: {e}")
        return
    
    # Verify bucket exists
    try:
        bucket = client.bucket(BUCKET_NAME)
        bucket.reload()  # Test access
        print(f"✅ Bucket access confirmed")
    except Exception as e:
        print(f"❌ Error accessing bucket: {e}")
        return
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload...")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        gcs_path = f"sref-images/{filename}"
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        try:
            # Upload to GCS
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(image_path, content_type='image/jpeg')
            
            # Generate public URL
            public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_path}"
            
            # Get file size
            file_size = os.path.getsize(image_path)
            
            image_mapping[filename] = {
                'url': public_url,
                'gcs_path': gcs_path,
                'size': file_size
            }
            print(f"  ✅ Uploaded: {public_url}")
            
        except Exception as e:
            print(f"  ❌ Failed to upload {filename}: {e}")
    
    # Save mapping to file
    mapping_file = "gcs_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n🎉 Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

if __name__ == "__main__":
    print("☁️  Google Cloud Storage Image Uploader")
    print("=" * 50)
    print(f"Using bucket: {BUCKET_NAME}")
    print("Using your existing gcloud authentication")
    print()
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Your Flask app will automatically use these GCS URLs")
        print("2. Deploy your app to Vercel")
        print("3. Images will be served from Google Cloud Storage")
        print("\nBenefits:")
        print("✅ Fast global CDN delivery")
        print("✅ Enterprise-grade reliability")
        print("✅ No additional costs (using your enterprise resource)")
        print("✅ Solves the 250MB Vercel deployment limit")

