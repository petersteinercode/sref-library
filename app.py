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
import numpy as np
from flask import Flask, render_template, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
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
    
    # Convert embeddings back to numpy arrays
    search_index = {}
    for sref_code, info in data.items():
        search_index[sref_code] = {
            'embedding': np.array(info['embedding']),
            'summary': info['summary'],
            'image_count': info['image_count'],
            'combined_captions': info['combined_captions']
        }
    
    print(f"Loaded search index with {len(search_index)} SREF styles")

def get_sref_thumbnails(sref_code, count=10):
    """Get thumbnail paths for a specific SREF code."""
    # Look for images with this SREF code
    pattern = os.path.join(OUTPUT_DIR, f"{sref_code}_*.png")
    image_files = glob.glob(pattern)
    
    # Sort to ensure consistent ordering
    image_files.sort()
    
    # Return up to 'count' thumbnails
    return image_files[:count]

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
        
        similarities.append({
            'sref_code': sref_code,
            'similarity': float(similarity),
            'summary': data['summary'],
            'image_count': data['image_count'],
            'combined_captions': data['combined_captions'],
            'thumbnails': []  # No thumbnails in deployment
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
            
            similarity = cosine_similarity([reference_embedding], [data['embedding']])[0][0]
            
            similarities.append({
                'sref_code': other_sref_code,
                'similarity': float(similarity),
                'summary': data['summary'],
                'image_count': data['image_count'],
                'combined_captions': data['combined_captions'],
                'thumbnails': []  # No thumbnails in deployment
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
