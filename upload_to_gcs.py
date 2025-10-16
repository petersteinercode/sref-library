#!/usr/bin/env python3
"""
Upload images to Google Cloud Storage

This script uploads all images from static/images/ to Google Cloud Storage
and creates a mapping file for the Flask app to use.

Prerequisites:
1. Create a Google Cloud account (free tier available)
2. Create a GCS bucket
3. Set up service account credentials
4. Install: pip install google-cloud-storage
"""

import os
import json
import glob
from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError

def setup_gcs_client():
    """Set up GCS client with credentials."""
    try:
        # Try to get credentials from environment variable or default location
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if credentials_path and os.path.exists(credentials_path):
            client = storage.Client.from_service_account_json(credentials_path)
        else:
            # Try default authentication (gcloud auth application-default login)
            client = storage.Client()
        
        # Test the connection
        list(client.list_buckets())
        return client
    except Exception as e:
        print(f"❌ Error setting up GCS client: {e}")
        print("Please ensure you have valid Google Cloud credentials")
        return None

def upload_image_to_gcs(gcs_client, bucket_name, image_path, gcs_path):
    """Upload a single image to GCS."""
    try:
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        # Upload with public read access
        blob.upload_from_filename(
            image_path,
            content_type='image/jpeg'
        )
        
        # Make the blob publicly readable
        blob.make_public()
        
        # Generate public URL
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        return public_url
    except GoogleCloudError as e:
        print(f"Error uploading {image_path}: {e}")
        return None

def upload_all_images():
    """Upload all images from static/images/ to GCS."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Set up GCS client
    gcs_client = setup_gcs_client()
    if not gcs_client:
        return
    
    # Get bucket name from environment
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    if not bucket_name:
        print("❌ GCS_BUCKET_NAME environment variable not set!")
        print("Please set your GCS bucket name")
        return
    
    # Verify bucket exists
    try:
        bucket = gcs_client.bucket(bucket_name)
        bucket.reload()  # Test access
        print(f"✅ Using GCS bucket: {bucket_name}")
    except NotFound:
        print(f"❌ Bucket {bucket_name} not found!")
        print("Please create the bucket first")
        return
    except Exception as e:
        print(f"❌ Error accessing bucket {bucket_name}: {e}")
        return
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload to GCS...")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        gcs_path = f"sref-images/{filename}"
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        public_url = upload_image_to_gcs(gcs_client, bucket_name, image_path, gcs_path)
        if public_url:
            # Get file size
            file_size = os.path.getsize(image_path)
            
            image_mapping[filename] = {
                'url': public_url,
                'gcs_path': gcs_path,
                'size': file_size
            }
            print(f"  ✅ Uploaded: {public_url}")
        else:
            print(f"  ❌ Failed to upload {filename}")
    
    # Save mapping to file
    mapping_file = "gcs_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✅ Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

def create_env_template():
    """Create a .env template file."""
    env_template = """# Google Cloud Storage Configuration
# Path to your service account JSON file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
# Your GCS bucket name
GCS_BUCKET_NAME=your-bucket-name-here
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("📄 Created .env.template file")
    print("Copy this to .env and fill in your GCS credentials")

def create_gcs_setup_instructions():
    """Print instructions for setting up GCS."""
    print("\n📋 Google Cloud Storage Setup Instructions:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable Cloud Storage API")
    print("4. Go to Cloud Storage → Buckets")
    print("5. Click 'Create bucket'")
    print("6. Choose a unique bucket name (e.g., 'sref-library-images')")
    print("7. Select a location (e.g., 'us-central1')")
    print("8. Choose 'Uniform' access control")
    print("9. Create bucket")
    print("\n🔐 Service Account Setup:")
    print("1. Go to IAM & Admin → Service Accounts")
    print("2. Click 'Create Service Account'")
    print("3. Name: 'sref-uploader'")
    print("4. Grant role: 'Storage Admin'")
    print("5. Create and download JSON key file")
    print("6. Set GOOGLE_APPLICATION_CREDENTIALS to the JSON file path")
    print("\n🚀 Alternative: Use gcloud CLI")
    print("1. Install gcloud CLI")
    print("2. Run: gcloud auth application-default login")
    print("3. This will use your user credentials automatically")

def create_bucket_public_policy():
    """Create a script to make bucket publicly readable."""
    script_content = '''#!/bin/bash
# Make GCS bucket publicly readable for images

BUCKET_NAME="your-bucket-name-here"

# Create a public access policy
cat > public_policy.json << EOF
{
  "bindings": [
    {
      "members": ["allUsers"],
      "role": "roles/storage.objectViewer"
    }
  ]
}
EOF

# Apply the policy
gsutil iam set public_policy.json gs://$BUCKET_NAME

echo "Bucket $BUCKET_NAME is now publicly readable"
'''
    
    with open('make_bucket_public.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('make_bucket_public.sh', 0o755)
    print("📄 Created make_bucket_public.sh script")
    print("Run this after creating your bucket to make it publicly readable")

if __name__ == "__main__":
    print("☁️  Google Cloud Storage Image Uploader")
    print("=" * 50)
    
    # Check if google-cloud-storage is installed
    try:
        from google.cloud import storage
        print("✅ Google Cloud Storage SDK found")
    except ImportError:
        print("❌ Google Cloud Storage SDK not found.")
        print("Please install: pip install google-cloud-storage")
        exit(1)
    
    # Create environment template and instructions
    create_env_template()
    create_gcs_setup_instructions()
    create_bucket_public_policy()
    
    # Check for environment variables
    if not os.getenv('GCS_BUCKET_NAME'):
        print("\n⚠️  GCS bucket name not found!")
        print("Please set GCS_BUCKET_NAME environment variable")
        print("See .env.template for required variables")
        exit(1)
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Update your Flask app to use GCS URLs")
        print("2. Deploy your app to Vercel")
        print("3. Images will be served from Google Cloud Storage")
        print("\nOptional: Set up Cloud CDN for faster delivery")
        print("\nBenefits:")
        print("✅ 5GB free storage (free tier)")
        print("✅ 1GB free egress per month")
        print("✅ Google's global infrastructure")
        print("✅ Can add Cloud CDN later")
        print("✅ Industry standard reliability")

