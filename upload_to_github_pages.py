#!/usr/bin/env python3
"""
Upload images to GitHub Pages

This script uploads all images from static/images/ to a GitHub repository
and creates a mapping file for the Flask app to use.

Prerequisites:
1. Create a GitHub repository (public for free hosting)
2. Enable GitHub Pages
3. Install: pip install PyGithub
"""

import os
import json
import glob
import base64
from github import Github
from github.GithubException import GithubException

def setup_github_client():
    """Set up GitHub client with token."""
    try:
        # Get token from environment variable
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("❌ GITHUB_TOKEN environment variable not found!")
            print("Please create a GitHub Personal Access Token")
            return None
        
        g = Github(token)
        
        # Test the connection
        user = g.get_user()
        print(f"✅ Connected to GitHub as: {user.login}")
        return g
    except Exception as e:
        print(f"❌ Error setting up GitHub client: {e}")
        return None

def upload_image_to_github(github_client, repo_name, image_path, github_path):
    """Upload a single image to GitHub repository."""
    try:
        repo = github_client.get_repo(repo_name)
        
        # Read image file
        with open(image_path, 'rb') as f:
            content = f.read()
        
        # Encode to base64
        content_b64 = base64.b64encode(content).decode('utf-8')
        
        # Upload to GitHub
        try:
            # Try to get existing file to get SHA
            existing_file = repo.get_contents(github_path)
            sha = existing_file.sha
            message = f"Update {os.path.basename(image_path)}"
        except GithubException:
            # File doesn't exist, create new
            sha = None
            message = f"Add {os.path.basename(image_path)}"
        
        result = repo.update_file(
            github_path,
            message,
            content_b64,
            sha=sha
        )
        
        # Generate raw URL for GitHub Pages
        raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{github_path}"
        return raw_url
    except Exception as e:
        print(f"Error uploading {image_path}: {e}")
        return None

def upload_all_images():
    """Upload all images from static/images/ to GitHub."""
    images_dir = "static/images"
    if not os.path.exists(images_dir):
        print(f"Images directory {images_dir} not found!")
        return
    
    # Set up GitHub client
    github_client = setup_github_client()
    if not github_client:
        return
    
    # Get repository name from environment
    repo_name = os.getenv('GITHUB_REPO_NAME')
    if not repo_name:
        print("❌ GITHUB_REPO_NAME environment variable not set!")
        print("Format: username/repository-name")
        return
    
    # Verify repository exists
    try:
        repo = github_client.get_repo(repo_name)
        print(f"✅ Using GitHub repository: {repo_name}")
    except GithubException as e:
        print(f"❌ Error accessing repository {repo_name}: {e}")
        return
    
    # Create image mapping
    image_mapping = {}
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
    total_files = len(image_files)
    
    print(f"Found {total_files} images to upload to GitHub...")
    print("⚠️  Note: GitHub has a 100MB file limit per file")
    print("⚠️  Large images may fail to upload")
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        github_path = f"images/{filename}"
        
        # Check file size (GitHub limit is 100MB)
        file_size = os.path.getsize(image_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            print(f"Skipping {filename} - too large ({file_size / 1024 / 1024:.1f}MB)")
            continue
        
        print(f"Uploading {i}/{total_files}: {filename}")
        
        raw_url = upload_image_to_github(github_client, repo_name, image_path, github_path)
        if raw_url:
            image_mapping[filename] = {
                'url': raw_url,
                'github_path': github_path,
                'size': file_size
            }
            print(f"  ✅ Uploaded: {raw_url}")
        else:
            print(f"  ❌ Failed to upload {filename}")
    
    # Save mapping to file
    mapping_file = "github_image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✅ Upload complete!")
    print(f"📁 {len(image_mapping)} images uploaded successfully")
    print(f"📄 Mapping saved to {mapping_file}")
    
    return image_mapping

def create_env_template():
    """Create a .env template file."""
    env_template = """# GitHub Configuration
# Create a Personal Access Token at https://github.com/settings/tokens
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO_NAME=username/repository-name
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("📄 Created .env.template file")
    print("Copy this to .env and fill in your GitHub credentials")

def create_github_setup_instructions():
    """Print instructions for setting up GitHub repository."""
    print("\n📋 GitHub Repository Setup Instructions:")
    print("1. Go to https://github.com/new")
    print("2. Create a new public repository (e.g., 'sref-images')")
    print("3. Go to repository Settings → Pages")
    print("4. Source: Deploy from a branch")
    print("5. Branch: main")
    print("6. Save")
    print("\n🔐 GitHub Token Setup:")
    print("1. Go to https://github.com/settings/tokens")
    print("2. Click 'Generate new token (classic)'")
    print("3. Select scopes: 'repo' (full control)")
    print("4. Generate token and copy it")
    print("\n📁 Repository Structure:")
    print("Your repo will have: /images/ folder with all JPG files")

if __name__ == "__main__":
    print("🐙 GitHub Pages Image Uploader")
    print("=" * 40)
    
    # Check if PyGithub is installed
    try:
        from github import Github
        print("✅ PyGithub SDK found")
    except ImportError:
        print("❌ PyGithub SDK not found.")
        print("Please install: pip install PyGithub")
        exit(1)
    
    # Create environment template and instructions
    create_env_template()
    create_github_setup_instructions()
    
    # Check for environment variables
    if not os.getenv('GITHUB_TOKEN') or not os.getenv('GITHUB_REPO_NAME'):
        print("\n⚠️  GitHub credentials or repository name not found!")
        print("Please set environment variables or create a .env file")
        print("See .env.template for required variables")
        exit(1)
    
    # Upload images
    mapping = upload_all_images()
    
    if mapping:
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Update your Flask app to use GitHub URLs")
        print("2. Deploy your app to Vercel")
        print("3. Images will be served from GitHub Pages")
        print("\nBenefits:")
        print("✅ Completely free")
        print("✅ Simple setup")
        print("✅ Good for static assets")
        print("✅ Version control for images")
        print("\nNote: GitHub has a 100MB file size limit per file")

