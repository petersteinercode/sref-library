# SREF Style Analysis and Search System

## Overview

This system analyzes and searches SREF (Style Reference) visual styles from Midjourney V7 collections. It creates semantic fingerprints for each SREF code and enables text-based search for visual styles.

## What Was Accomplished

### 1. Image Processing Pipeline

- **Processed 4 PDF collections**: Texture & Effect, For Designers, Illustration, Photorealism
- **Generated 2,320 images**: 10 crops per page × 58 pages × 4 PDFs
- **Extracted 232 unique SREF codes**: Each representing a distinct visual style
- **Created comprehensive metadata**: All images catalogued with coordinates and SREF information

### 2. SREF Analysis System

- **CLIP Embeddings**: Generated visual embeddings for each of the 2,320 images
- **BLIP Captions**: Created descriptive captions for each image
- **Semantic Fingerprints**: Averaged embeddings per SREF to create consistent style representations
- **Style Summaries**: Generated thematic summaries for each SREF based on caption analysis

### 3. Search Functionality

- **Text-to-Visual Search**: Find SREF styles based on written descriptions
- **Similarity Matching**: Uses cosine similarity between query and SREF embeddings
- **Interactive Interface**: Command-line tool for searching styles
- **Batch Processing**: Support for multiple queries at once

## Files Created

### Core Scripts

- `process_one_page-v2.py` - Main image processing pipeline
- `analyze_sref_styles.py` - SREF analysis and embedding generation
- `search_sref.py` - Interactive search interface

### Data Files

- `output_test/metadata.csv` - Complete metadata for all 2,320 images
- `sref_analysis/sref_embeddings.json` - Full analysis data (3.6MB)
- `sref_analysis/sref_search_index.json` - Search index (3.4MB)

### Output Images

- `output_test/` - 2,320 cropped images organized by SREF code

## Usage Examples

### Interactive Search

```bash
python3 search_sref.py
```

### Batch Search

```bash
python3 search_sref.py "abstract art" "minimalist design" "photorealistic portrait"
```

### Example Search Results

**Query: "abstract colorful art"**

- SREF 724797448 (similarity: 0.293) - Key themes: painting, background, flowers, colors
- SREF 1513021496 (similarity: 0.279) - Key themes: painting, woman, man, colorful, blue

**Query: "minimalist design"**

- SREF 2293543416 (similarity: 0.312) - Key themes: man, white, background, robe
- SREF 3095273558 (similarity: 0.310) - Key themes: hello, white, black, background

**Query: "photorealistic portrait"**

- SREF 248055342 (similarity: 0.298) - Key themes: white, black, photo, man, standing
- SREF 424949549 (similarity: 0.296) - Key themes: drawing, man, green, holding, car

## Technical Details

### Grid Configuration

- **Starting position**: (259, 259)
- **Cell dimensions**: 1476 × 2175 pixels each
- **Padding**: 30px between cells
- **Grid layout**: 2×5 (10 crops per page)

### Models Used

- **CLIP**: OpenAI's CLIP-ViT-Base-Patch32 for visual-text embeddings
- **BLIP**: Salesforce's BLIP for image captioning
- **Scikit-learn**: For cosine similarity calculations

### Performance

- **Processing time**: ~3-4 minutes for full analysis
- **Memory usage**: ~1.2GB during processing
- **Search speed**: Near-instantaneous for text queries

## Best Practices Workflow Implemented

1. ✅ **Grouped images by SREF**: Each SREF folder contains 10 related images
2. ✅ **Generated CLIP embeddings**: Visual embeddings for all 2,320 images
3. ✅ **Averaged embeddings**: One combined embedding per SREF (232 total)
4. ✅ **Generated captions**: BLIP captions for each image
5. ✅ **Created summaries**: Thematic analysis of combined captions
6. ✅ **Built search index**: Semantic fingerprints for text-based search

## Future Enhancements

- **Web interface**: Browser-based search interface
- **Image similarity**: Find similar SREFs based on uploaded images
- **Style clustering**: Group similar SREFs together
- **Export functionality**: Export search results with image previews
- **Advanced filtering**: Filter by collection, similarity threshold, etc.

## Dependencies

```bash
pip install torch torchvision transformers pillow pandas numpy scikit-learn PyPDF2 pdf2image
```

## System Requirements

- **Python 3.8+**
- **8GB+ RAM** (for model loading)
- **2GB+ disk space** (for models and data)
- **macOS/Linux** (tested on macOS with Apple Silicon)
