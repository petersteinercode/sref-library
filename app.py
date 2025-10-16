#!/usr/bin/env python3
"""
SREF Search Web Application

Flask-based web interface for searching SREF visual styles.
Provides a clean UI for text-based search with thumbnail results.

Usage:
    python3 app.py
    Then visit http://localhost:5000
"""

import os
import json
import math
from flask import Flask, render_template, request, jsonify
import glob

# Configuration
SREF_ANALYSIS_DIR = "sref_analysis"
SEARCH_INDEX_FILE = "sref_search_index.json"
OUTPUT_DIR = "output_test"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

# Initialize Flask app
app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)

# Global variables for search index
search_index = None

def cosine_similarity_python(a, b):
    """Simple cosine similarity using pure Python."""
    # Calculate dot product
    dot_product = sum(x * y for x, y in zip(a, b))
    
    # Calculate magnitudes
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))
    
    # Avoid division by zero
    if magnitude_a == 0 or magnitude_b == 0:
        return 0
    
    return dot_product / (magnitude_a * magnitude_b)

def load_models():
    """Load models for text processing (simplified for deployment)."""
    print("Models loading skipped for deployment - using pre-computed embeddings only")

def load_search_index():
    """Load the search index from file."""
    global search_index
    
    index_path = os.path.join(SREF_ANALYSIS_DIR, SEARCH_INDEX_FILE)
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Search index not found: {index_path}")
    
    with open(index_path, 'r') as f:
        data = json.load(f)
    
    # Convert embeddings back to lists (no numpy needed)
    search_index = {}
    for sref_code, info in data.items():
        search_index[sref_code] = {
            'embedding': list(info['embedding']),  # Convert to list instead of numpy array
            'summary': info['summary'],
            'image_count': info['image_count'],
            'combined_captions': info['combined_captions']
        }
    
    print(f"Loaded search index with {len(search_index)} SREF styles")

def load_image_mapping():
    """Load the image mapping from any available provider."""
    # Try different mapping files in order of preference
    mapping_files = [
        "gcs_image_mapping.json",         # Google Cloud Storage (user's choice)
        "cloudinary_image_mapping.json",  # Cloudinary
        "s3_image_mapping.json",          # AWS S3
        "github_image_mapping.json",      # GitHub Pages
        "blob_image_mapping.json"         # Vercel Blob (if available)
    ]
    
    for mapping_file in mapping_files:
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
                print(f"Loaded image mapping from {mapping_file}")
                return mapping
    
    return {}

def get_sref_thumbnails(sref_code, count=10):
    """Get thumbnail paths for a specific SREF code."""
    # First try to load external image mapping (Cloudinary, S3, GitHub, etc.)
    image_mapping = load_image_mapping()
    
    if image_mapping:
        # Use external URLs if mapping exists
        thumbnails = []
        for i in range(1, min(count + 1, 11)):
            filename = f"{sref_code}_{i:02d}.jpg"
            if filename in image_mapping:
                # Handle different mapping formats
                if isinstance(image_mapping[filename], dict):
                    thumbnails.append(image_mapping[filename]['url'])
                else:
                    thumbnails.append(image_mapping[filename])
        return thumbnails
    
    # Fallback to local images (for development)
    static_images_dir = os.path.join(STATIC_DIR, "images")
    if os.path.exists(static_images_dir):
        pattern = os.path.join(static_images_dir, f"{sref_code}_*.jpg")
        image_files = glob.glob(pattern)
        image_files.sort()
        return image_files[:count]
    
    # Return placeholder image names if no images found
    return [f"{sref_code}_{i:02d}.jpg" for i in range(1, min(count + 1, 11))]

def search_sref_styles(query_text, top_k=50):
    """Search for SREF styles based on text query (simplified version)."""
    if not search_index:
        return []
    
    # Simple text-based search using summaries and captions
    query_lower = query_text.lower()
    similarities = []
    
    for sref_code, data in search_index.items():
        # Calculate text similarity based on keyword matching
        summary_text = data['summary'].lower()
        captions_text = data['combined_captions'].lower()
        combined_text = f"{summary_text} {captions_text}"
        
        # Simple keyword matching score
        query_words = query_lower.split()
        matches = sum(1 for word in query_words if word in combined_text)
        similarity = matches / len(query_words) if query_words else 0
        
        # Boost score if exact phrase matches
        if query_lower in combined_text:
            similarity += 0.5
        
        # Get thumbnails for this SREF
        thumbnails = get_sref_thumbnails(sref_code, count=10)
        
        # Handle both blob URLs and local file paths
        thumbnail_names = []
        for thumb in thumbnails:
            if thumb.startswith('http'):
                # It's a blob URL, use the full URL
                thumbnail_names.append(thumb)
            else:
                # It's a local file path, use just the filename
                thumbnail_names.append(os.path.basename(thumb))
        
        similarities.append({
            'sref_code': sref_code,
            'similarity': float(similarity),
            'summary': data['summary'],
            'image_count': data['image_count'],
            'combined_captions': data['combined_captions'],
            'thumbnails': thumbnail_names
        })
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities[:top_k]

@app.route('/')
def index():
    """Main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """API endpoint for SREF search."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform search
        results = search_sref_styles(query, top_k=50)
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/similar', methods=['POST'])
def find_similar():
    """API endpoint for finding similar SREFs based on vector similarity."""
    try:
        data = request.get_json()
        sref_code = data.get('sref_code', '').strip()
        
        if not sref_code:
            return jsonify({'error': 'SREF code is required'}), 400
        
        if not search_index or sref_code not in search_index:
            return jsonify({'error': f'SREF code {sref_code} not found'}), 404
        
        # Get the embedding for the reference SREF
        reference_embedding = search_index[sref_code]['embedding']
        
        # Calculate similarities with all other SREFs using embeddings
        similarities = []
        for other_sref_code, data in search_index.items():
            if other_sref_code == sref_code:
                continue  # Skip the reference SREF itself
            
            similarity = cosine_similarity_python(reference_embedding, data['embedding'])
            
            # Get thumbnails for this SREF
            thumbnails = get_sref_thumbnails(other_sref_code, count=10)
            
            # Handle both blob URLs and local file paths
            thumbnail_names = []
            for thumb in thumbnails:
                if thumb.startswith('http'):
                    # It's a blob URL, use the full URL
                    thumbnail_names.append(thumb)
                else:
                    # It's a local file path, use just the filename
                    thumbnail_names.append(os.path.basename(thumb))
            
            similarities.append({
                'sref_code': other_sref_code,
                'similarity': float(similarity),
                'summary': data['summary'],
                'image_count': data['image_count'],
                'combined_captions': data['combined_captions'],
                'thumbnails': thumbnail_names
            })
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top 20 most similar SREFs
        top_similar = similarities[:20]
        
        return jsonify({
            'reference_sref': sref_code,
            'results': top_similar,
            'total_found': len(top_similar)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tags')
def get_top_tags():
    """API endpoint to get curated tags for user interface."""
    try:
        # Load curated tags from JSON file
        curated_tags_path = os.path.join(os.path.dirname(__file__), 'curated_tags.json')
        
        if not os.path.exists(curated_tags_path):
            # Fallback to hardcoded curated tags if file doesn't exist
            curated_tags = [
                "painting", "illustration", "drawing", "poster",
                "white", "blue", "black", "red", "green", "pink", "purple", "yellow", "orange", "gold",
                "flowers", "sky", "water", "field", "ocean", "beach", "street", "night", "lights", "air", "tree", "snow", "flower", "bird", "cat",
                "close", "colorful", "city", "group", "face", "bunch"
            ]
        else:
            with open(curated_tags_path, 'r') as f:
                curated_data = json.load(f)
                curated_tags = curated_data['all_tags']
        
        return jsonify({
            'tags': curated_tags,
            'total_unique_tags': len(curated_tags),
            'categories': {
                'art_media_styles': curated_data.get('art_media_styles', []),
                'colors': curated_data.get('colors', []),
                'nature_environment': curated_data.get('nature_environment', []),
                'descriptive_terms': curated_data.get('descriptive_terms', [])
            } if os.path.exists(curated_tags_path) else {}
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'sref_count': len(search_index) if search_index else 0,
        'models_loaded': True  # Simplified for deployment
    })

def create_directories():
    """Create necessary directories."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)

def initialize_app():
    """Initialize the Flask application (for Vercel deployment)."""
    print("Initializing SREF Search Web Application...")
    
    # Create directories
    create_directories()
    
    # Load models and search index
    try:
        load_models()
        load_search_index()
        print("Application initialized successfully!")
    except Exception as e:
        print(f"Error loading models or search index: {e}")
        print("Please run analyze_sref_styles.py first to create the search index.")
        raise e

def main():
    """Initialize and run the Flask application."""
    initialize_app()
    
    print("Starting web server...")
    print("Visit http://localhost:5002 to use the SREF search interface")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5002, debug=True)

# Initialize app for Vercel deployment
if __name__ == "__main__":
    main()
else:
    # This runs when deployed to Vercel
    try:
        initialize_app()
    except Exception as e:
        print(f"Failed to initialize app: {e}")
        # Continue anyway - some endpoints might still work
