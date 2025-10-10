#!/usr/bin/env python3
"""
SREF Style Search Interface

Interactive search tool for finding SREF styles based on text descriptions.
Uses the pre-computed embeddings and search index from analyze_sref_styles.py

Usage:
    python3 search_sref.py
"""

import json
import os
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
SREF_ANALYSIS_DIR = "sref_analysis"
SEARCH_INDEX_FILE = "sref_search_index.json"
OUTPUT_DIR = "output_test"

# Load models
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading models on {DEVICE}...")

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.to(DEVICE)

def load_search_index():
    """Load the search index from file."""
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
    
    return search_index

def search_sref_styles(query_text, search_index, top_k=10):
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
            'image_count': data['image_count'],
            'combined_captions': data['combined_captions']
        })
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities[:top_k]

def display_results(results, query):
    """Display search results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"SEARCH RESULTS FOR: '{query}'")
    print(f"{'='*60}")
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. SREF {result['sref_code']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Images: {result['image_count']}")
        print(f"   Summary: {result['summary']}")
        
        # Show first few words of combined captions
        caption_preview = result['combined_captions'][:100] + "..." if len(result['combined_captions']) > 100 else result['combined_captions']
        print(f"   Captions: {caption_preview}")

def interactive_search():
    """Interactive search interface."""
    print("Loading SREF search index...")
    try:
        search_index = load_search_index()
        print(f"Loaded {len(search_index)} SREF styles")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run analyze_sref_styles.py first to create the search index.")
        return
    
    print(f"\n{'='*60}")
    print("SREF STYLE SEARCH INTERFACE")
    print(f"{'='*60}")
    print("Enter text descriptions to find matching SREF styles.")
    print("Examples:")
    print("  - 'abstract art'")
    print("  - 'photorealistic portrait'")
    print("  - 'geometric design'")
    print("  - 'nature landscape'")
    print("  - 'minimalist style'")
    print("  - 'colorful painting'")
    print("  - 'dark moody atmosphere'")
    print("\nType 'quit' to exit.")
    print(f"{'='*60}")
    
    while True:
        try:
            query = input("\nEnter your search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                print("Please enter a search query.")
                continue
            
            print(f"\nSearching for: '{query}'...")
            results = search_sref_styles(query, search_index, top_k=5)
            display_results(results, query)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error during search: {e}")

def batch_search(queries):
    """Search for multiple queries at once."""
    print("Loading SREF search index...")
    try:
        search_index = load_search_index()
        print(f"Loaded {len(search_index)} SREF styles")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run analyze_sref_styles.py first to create the search index.")
        return
    
    for query in queries:
        print(f"\nSearching for: '{query}'...")
        results = search_sref_styles(query, search_index, top_k=3)
        display_results(results, query)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Batch mode - search for provided queries
        queries = sys.argv[1:]
        batch_search(queries)
    else:
        # Interactive mode
        interactive_search()
