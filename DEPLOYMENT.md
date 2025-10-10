# SREF Library - Vercel Deployment Guide

## Overview

This guide will help you deploy your SREF (Style Reference) search application to Vercel.

## ⚠️ Important: Data Storage Considerations

Your application has **1.9GB of data files** that cannot be deployed directly to Vercel due to size limits:

- `output_test/` (1.1GB) - Image thumbnails
- `assets/` (855MB) - PDF files
- `sref_analysis/` (6.9MB) - Search index and embeddings

## Deployment Options

### Option 1: External Data Storage (Recommended)

Store your data files externally and modify the app to fetch them:

1. **Upload data to cloud storage:**

   - AWS S3, Google Cloud Storage, or similar
   - Upload `sref_analysis/` folder (contains search index)
   - Upload `output_test/` folder (contains thumbnails)

2. **Modify app.py to fetch data from cloud storage:**
   ```python
   # Add cloud storage client initialization
   # Modify load_search_index() to download from cloud
   # Modify get_sref_thumbnails() to fetch from cloud
   ```

### Option 2: Minimal Deployment (Search Only)

Deploy with just the search functionality:

1. Keep only `sref_analysis/` folder (6.9MB - within limits)
2. Remove image thumbnails functionality
3. Deploy as search-only interface

### Option 3: Hybrid Approach

- Deploy search functionality to Vercel
- Host images on a separate CDN
- Link to external image URLs

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Vercel deployment"
```

### 2. Install Vercel CLI

```bash
npm i -g vercel
```

### 3. Deploy to Vercel

```bash
# From your project directory
vercel

# Follow the prompts:
# - Link to existing project or create new one
# - Choose your team/account
# - Confirm project settings
```

### 4. Configure Environment Variables (if needed)

In Vercel dashboard:

- Go to your project settings
- Add environment variables for cloud storage credentials

### 5. Test Deployment

Visit your Vercel URL to test the application.

## Files Created for Deployment

- `requirements.txt` - Python dependencies
- `vercel.json` - Vercel configuration
- `wsgi.py` - WSGI entry point
- `.vercelignore` - Excludes large files from deployment

## Troubleshooting

### Common Issues:

1. **Deployment timeout**: Increase `maxDuration` in vercel.json
2. **Memory issues**: Consider upgrading Vercel plan
3. **Missing data**: Ensure data files are accessible via cloud storage

### Performance Optimization:

- Use Vercel's Pro plan for better performance
- Consider caching strategies for search results
- Optimize image sizes and formats

## Next Steps

1. Choose your deployment approach
2. Set up external data storage if needed
3. Modify the app accordingly
4. Deploy and test

For questions or issues, refer to Vercel's documentation or create an issue in your repository.
