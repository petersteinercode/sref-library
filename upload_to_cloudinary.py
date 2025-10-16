#!/usr/bin/env python3
"""
Upload images to Cloudinary

This script uploads all images from static/images/ to Cloudinary
and creates a mapping file for the Flask app to use.

Prerequisites:
1. Create a free Cloudinary account at https://cloudinary.com
2. Get your Cloud Name, API Key, and API Secret from the dashboard
3. Install: pip install cloudinary
"""

import os
import json
import glob
from cloudinary import CloudinaryImage, uploader
from cloudinary.utils import cloudinary_url

def setup_cloudinary():
    """Set up Cloudinary configuration."""
    import cloudinary
    from cloudinary import config
    
    # You can set these as environment variables or hardcode them
    # For security, use environment variables in production
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME', 'your_cloud_name')
    api_key = os.getenv('CLOUDINARY_API_KEY', 'your_api_key')
    api_secret = os.getenv('CLOUDINARY_API_SECRET', 'your_api_secret')
    
    config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    
    return cloud_name

def upload_image_to_cloudinary(image_path, public_id):
    """Upload a single image to Cloudinary."""
    try:
        result = uploader.upload(
            image_path,
            public_id=public_id,
            folder="sref-images",  # Organize images in a folder
            resource_type="image",
            overwrite=True,
            invalidate=True
        )
        return result
    except Exception as e:
        print(f"Error uploading {image_path}: {e}")
        return None

def upload_all_images():
    """Upload all images from static/images/ to Cloudinary."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Set up Cloudinary
    cloud_name = setup_cloudinary()
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload to Cloudinary...")
    print(f"Cloud Name: {cloud_name}")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        # Remove .jpg extension for public_id
        public_id = f"sref-images/{filename[:-4]}"
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        result = upload_image_to_cloudinary(image_path, public_id)
        if result:
            # Generate optimized URL
            optimized_url, _ = cloudinary_url(
                public_id,
                width=300,  # Thumbnail size
                height=300,
                crop="fill",
                quality="auto",
                format="auto"
            )
            
            image_mapping[filename] = {
                'url': optimized_url,
                'public_id': public_id,
                'original_url': result['secure_url'],
                'size': result['bytes']
            }
            print(f"  ✅ Uploaded: {optimized_url}")
        else:
            print(f"  ❌ Failed to upload {filename}")
    
    # Save mapping to file
    mapping_file = "cloudinary_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✅ Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

def create_env_template():
    """Create a .env template file."""
    env_template = """# Cloudinary Configuration
# Get these values from https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("📄 Created .env.template file")
    print("Copy this to .env and fill in your Cloudinary credentials")

if __name__ == "__main__":
    print("☁️  Cloudinary Image Uploader")
    print("=" * 40)
    
    # Check if cloudinary is installed
    try:
        import cloudinary
        print("✅ Cloudinary SDK found")
    except ImportError:
        print("❌ Cloudinary SDK not found.")
        print("Please install: pip install cloudinary")
        exit(1)
    
    # Create environment template
    create_env_template()
    
    # Check for environment variables
    if not os.getenv('CLOUDINARY_CLOUD_NAME'):
        print("\n⚠️  Cloudinary credentials not found!")
        print("Please set environment variables or create a .env file")
        print("See .env.template for required variables")
        print("\nTo get your credentials:")
        print("1. Go to https://cloudinary.com/console")
        print("2. Copy your Cloud Name, API Key, and API Secret")
        print("3. Set them as environment variables or in .env file")
        exit(1)
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Update your Flask app to use Cloudinary URLs")
        print("2. Deploy your app to Vercel")
        print("3. Images will be served from Cloudinary's global CDN")
        print("\nBenefits:")
        print("✅ Automatic image optimization")
        print("✅ Global CDN delivery")
        print("✅ 25GB free storage")
        print("✅ On-the-fly transformations")

