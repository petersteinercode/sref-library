#!/usr/bin/env python3
"""
SREF Style Analysis and Search System

This script analyzes SREF visual styles by:
1. Grouping images by SREF code
2. Generating CLIP embeddings for each image
3. Averaging embeddings per SREF to create semantic fingerprints
4. Generating captions and summaries for each SREF
5. Creating search functionality for visual style matching

Requirements:
    pip install torch torchvision transformers pillow pandas numpy scikit-learn
"""

import os
import pandas as pd
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from sklearn.metrics.pairwise import cosine_similarity
import json
from collections import defaultdict
import re

# Configuration
OUTPUT_DIR = "output_test"
SREF_ANALYSIS_DIR = "sref_analysis"
EMBEDDINGS_FILE = "sref_embeddings.json"
SEARCH_INDEX_FILE = "sref_search_index.json"

# Model configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Initialize models
print("Loading CLIP model...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.to(DEVICE)

print("Loading BLIP model...")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model.to(DEVICE)

def load_metadata():
    """Load the metadata CSV to get SREF groupings."""
    metadata_path = os.path.join(OUTPUT_DIR, "metadata.csv")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    print(f"Loaded metadata with {len(df)} records")
    return df

def group_images_by_sref(df):
    """Group images by SREF code."""
    sref_groups = defaultdict(list)
    
    for _, row in df.iterrows():
        sref = row['sref']
        filename = row['filename']
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(filepath):
            sref_groups[sref].append({
                'filename': filename,
                'filepath': filepath,
                'page': row['page'],
                'row': row['row'],
                'col': row['col']
            })
        else:
            print(f"Warning: Image file not found: {filepath}")
    
    print(f"Grouped images into {len(sref_groups)} SREF categories")
    return sref_groups

def generate_clip_embedding(image_path):
    """Generate CLIP embedding for a single image."""
    try:
        image = Image.open(image_path).convert('RGB')
        inputs = clip_processor(images=image, return_tensors="pt").to(DEVICE)
        
        with torch.no_grad():
            image_features = clip_model.get_image_features(**inputs)
            # Normalize the features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def generate_blip_caption(image_path):
    """Generate BLIP caption for a single image."""
    try:
        image = Image.open(image_path).convert('RGB')
        inputs = blip_processor(image, return_tensors="pt").to(DEVICE)
        
        with torch.no_grad():
            out = blip_model.generate(**inputs, max_length=50, num_beams=5)
        
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"Error generating caption for {image_path}: {e}")
        return ""

def analyze_sref_group(sref_code, image_group):
    """Analyze a single SREF group to create semantic fingerprint."""
    print(f"Analyzing SREF {sref_code} with {len(image_group)} images...")
    
    embeddings = []
    captions = []
    
    for img_info in image_group:
        # Generate CLIP embedding
        embedding = generate_clip_embedding(img_info['filepath'])
        if embedding is not None:
            embeddings.append(embedding)
        
        # Generate BLIP caption
        caption = generate_blip_caption(img_info['filepath'])
        if caption:
            captions.append(caption)
    
    if not embeddings:
        print(f"Warning: No valid embeddings for SREF {sref_code}")
        return None
    
    # Average the embeddings to create semantic fingerprint
    avg_embedding = np.mean(embeddings, axis=0)
    
    # Combine and summarize captions
    combined_captions = " ".join(captions)
    summary = summarize_captions(combined_captions)
    
    return {
        'sref_code': sref_code,
        'embedding': avg_embedding.tolist(),
        'individual_captions': captions,
        'combined_captions': combined_captions,
        'summary': summary,
        'image_count': len(image_group),
        'image_files': [img['filename'] for img in image_group]
    }

def summarize_captions(captions_text):
    """Simple summarization of captions by extracting common themes."""
    # Split into words and count frequency
    words = re.findall(r'\b\w+\b', captions_text.lower())
    
    # Filter out common words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequency
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top words
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Create summary
    summary_parts = []
    for word, count in top_words:
        if count > 1:  # Only include words that appear multiple times
            summary_parts.append(f"{word} ({count})")
    
    if summary_parts:
        return f"Key themes: {', '.join(summary_parts[:5])}"
    else:
        return "Visual style analysis completed"

def create_search_index(sref_analyses):
    """Create search index for SREF styles."""
    search_index = {}
    
    for analysis in sref_analyses:
        if analysis is None:
            continue
            
        sref_code = analysis['sref_code']
        embedding = np.array(analysis['embedding'])
        
        search_index[sref_code] = {
            'embedding': embedding,
            'summary': analysis['summary'],
            'image_count': analysis['image_count'],
            'combined_captions': analysis['combined_captions']
        }
    
    return search_index

def search_sref_styles(query_text, search_index, top_k=5):
    """Search for SREF styles based on text query."""
    if not search_index:
        print("No search index available")
        return []
    
    # Generate embedding for query text
    text_inputs = clip_processor(text=[query_text], return_tensors="pt", padding=True, truncation=True).to(DEVICE)
    
    with torch.no_grad():
        text_features = clip_model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    
    query_embedding = text_features.cpu().numpy().flatten()
    
    # Calculate similarities
    similarities = []
    for sref_code, data in search_index.items():
        similarity = cosine_similarity([query_embedding], [data['embedding']])[0][0]
        similarities.append({
            'sref_code': sref_code,
            'similarity': similarity,
            'summary': data['summary'],
            'image_count': data['image_count']
        })
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities[:top_k]

def main():
    """Main analysis workflow."""
    print("Starting SREF style analysis...")
    
    # Create analysis directory
    os.makedirs(SREF_ANALYSIS_DIR, exist_ok=True)
    
    # Load metadata and group images
    df = load_metadata()
    sref_groups = group_images_by_sref(df)
    
    # Analyze each SREF group
    sref_analyses = []
    for sref_code, image_group in sref_groups.items():
        analysis = analyze_sref_group(sref_code, image_group)
        sref_analyses.append(analysis)
    
    # Filter out None results
    valid_analyses = [a for a in sref_analyses if a is not None]
    
    print(f"Successfully analyzed {len(valid_analyses)} SREF styles")
    
    # Save embeddings and analysis
    embeddings_path = os.path.join(SREF_ANALYSIS_DIR, EMBEDDINGS_FILE)
    with open(embeddings_path, 'w') as f:
        json.dump(valid_analyses, f, indent=2)
    print(f"Saved embeddings to {embeddings_path}")
    
    # Create and save search index
    search_index = create_search_index(valid_analyses)
    search_index_path = os.path.join(SREF_ANALYSIS_DIR, SEARCH_INDEX_FILE)
    
    # Convert numpy arrays to lists for JSON serialization
    search_index_serializable = {}
    for sref_code, data in search_index.items():
        search_index_serializable[sref_code] = {
            'embedding': data['embedding'].tolist(),
            'summary': data['summary'],
            'image_count': data['image_count'],
            'combined_captions': data['combined_captions']
        }
    
    with open(search_index_path, 'w') as f:
        json.dump(search_index_serializable, f, indent=2)
    print(f"Saved search index to {search_index_path}")
    
    # Test search functionality
    print("\n" + "="*50)
    print("Testing search functionality...")
    print("="*50)
    
    test_queries = [
        "abstract art",
        "photorealistic portrait",
        "geometric design",
        "nature landscape",
        "minimalist style"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_sref_styles(query, search_index, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. SREF {result['sref_code']} (similarity: {result['similarity']:.3f})")
            print(f"     {result['summary']}")
    
    print(f"\nAnalysis complete! Check {SREF_ANALYSIS_DIR}/ for results.")

if __name__ == "__main__":
    main()
