#!/usr/bin/env python3
"""
Upload images to AWS S3

This script uploads all images from static/images/ to AWS S3
and creates a mapping file for the Flask app to use.

Prerequisites:
1. Create an AWS account (free tier available)
2. Create an S3 bucket
3. Set up AWS credentials
4. Install: pip install boto3
"""

import os
import json
import glob
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def setup_s3_client():
    """Set up S3 client with credentials."""
    try:
        # Try to get credentials from environment variables or AWS config
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Test the connection
        s3_client.list_buckets()
        return s3_client
    except NoCredentialsError:
        print("❌ AWS credentials not found!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return None
    except Exception as e:
        print(f"❌ Error setting up S3 client: {e}")
        return None

def upload_image_to_s3(s3_client, bucket_name, image_path, s3_key):
    """Upload a single image to S3."""
    try:
        # Upload with public read access
        s3_client.upload_file(
            image_path,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'image/jpeg'
            }
        )
        
        # Generate public URL
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return public_url
    except ClientError as e:
        print(f"Error uploading {image_path}: {e}")
        return None

def upload_all_images():
    """Upload all images from static/images/ to S3."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Set up S3 client
    s3_client = setup_s3_client()
    if not s3_client:
        return
    
    # Get bucket name from environment or prompt
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        print("❌ S3_BUCKET_NAME environment variable not set!")
        print("Please set your S3 bucket name")
        return
    
    # Verify bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Using S3 bucket: {bucket_name}")
    except ClientError as e:
        print(f"❌ Error accessing bucket {bucket_name}: {e}")
        return
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload to S3...")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        s3_key = f"sref-images/{filename}"
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        public_url = upload_image_to_s3(s3_client, bucket_name, image_path, s3_key)
        if public_url:
            # Get file size
            file_size = os.path.getsize(image_path)
            
            image_mapping[filename] = {
                'url': public_url,
                's3_key': s3_key,
                'size': file_size
            }
            print(f"  ✅ Uploaded: {public_url}")
        else:
            print(f"  ❌ Failed to upload {filename}")
    
    # Save mapping to file
    mapping_file = "s3_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✅ Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

def create_env_template():
    """Create a .env template file."""
    env_template = """# AWS S3 Configuration
# Get these from your AWS Console
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name-here
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("📄 Created .env.template file")
    print("Copy this to .env and fill in your AWS credentials")

def create_s3_bucket_instructions():
    """Print instructions for creating an S3 bucket."""
    print("\n📋 S3 Bucket Setup Instructions:")
    print("1. Go to https://console.aws.amazon.com/s3/")
    print("2. Click 'Create bucket'")
    print("3. Choose a unique bucket name (e.g., 'sref-library-images')")
    print("4. Select a region (e.g., 'US East (N. Virginia)')")
    print("5. Uncheck 'Block all public access' (we need public read access)")
    print("6. Acknowledge the warning about public access")
    print("7. Click 'Create bucket'")
    print("\n🔐 AWS Credentials Setup:")
    print("1. Go to https://console.aws.amazon.com/iam/")
    print("2. Click 'Users' → 'Create user'")
    print("3. Attach policy: 'AmazonS3FullAccess'")
    print("4. Create access key and download credentials")

if __name__ == "__main__":
    print("☁️  AWS S3 Image Uploader")
    print("=" * 40)
    
    # Check if boto3 is installed
    try:
        import boto3
        print("✅ Boto3 SDK found")
    except ImportError:
        print("❌ Boto3 SDK not found.")
        print("Please install: pip install boto3")
        exit(1)
    
    # Create environment template and instructions
    create_env_template()
    create_s3_bucket_instructions()
    
    # Check for environment variables
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('S3_BUCKET_NAME'):
        print("\n⚠️  AWS credentials or bucket name not found!")
        print("Please set environment variables or create a .env file")
        print("See .env.template for required variables")
        exit(1)
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Update your Flask app to use S3 URLs")
        print("2. Deploy your app to Vercel")
        print("3. Images will be served from S3")
        print("\nOptional: Set up CloudFront CDN for faster delivery")
        print("\nBenefits:")
        print("✅ Industry standard storage")
        print("✅ 5GB free storage (free tier)")
        print("✅ Highly reliable")
        print("✅ Can add CloudFront CDN later")

