# SREF Tag System Documentation

## Overview

The SREF library uses a curated tag system to help users discover visual styles. The tag system focuses on artistic styles, colors, nature/environment, and descriptive terms, excluding object-specific tags to maintain focus on visual style rather than content.

## Tag Categories

### 🎨 Art Media & Styles (4 tags)

- **painting** - Traditional painted artwork
- **illustration** - Digital or hand-drawn illustrations
- **drawing** - Pencil, pen, or other drawing media
- **poster** - Poster-style graphics and designs

### 🌈 Colors (10 tags)

- **white** - White color schemes
- **blue** - Blue color schemes
- **black** - Black color schemes
- **red** - Red color schemes
- **green** - Green color schemes
- **pink** - Pink color schemes
- **purple** - Purple color schemes
- **yellow** - Yellow color schemes
- **orange** - Orange color schemes
- **gold** - Gold color schemes

### 🌿 Nature & Environment (15 tags)

- **flowers** - Floral elements and arrangements
- **sky** - Sky and atmospheric elements
- **water** - Water features and bodies
- **field** - Open fields and landscapes
- **ocean** - Ocean and sea scenes
- **beach** - Beach and coastal scenes
- **street** - Street scenes and urban environments
- **night** - Nighttime scenes
- **lights** - Lighting effects and illumination
- **air** - Atmospheric and aerial elements
- **tree** - Trees and forest elements
- **snow** - Snow and winter scenes
- **flower** - Individual flower elements
- **bird** - Bird subjects and elements
- **cat** - Cat subjects and elements

### 🔍 Descriptive Terms (6 tags)

- **close** - Close-up views and details
- **colorful** - Vibrant and multi-colored scenes
- **city** - Urban and city environments
- **group** - Group compositions and arrangements
- **face** - Facial features and portraits
- **bunch** - Grouped or clustered elements

## Implementation

### Backend

- Tags are served via `/tags` endpoint
- Curated list is stored in `curated_tags.json`
- Fallback to hardcoded list if file is missing
- Returns both flat list and categorized structure

### Frontend

- Tags are loaded dynamically on page load
- Shuffle button randomizes the displayed tags
- Clicking a tag performs a search for that term
- Tags are displayed as clickable buttons

### Tag Selection Criteria

Tags were selected based on:

1. **Frequency** - Must appear in at least 2 SREF summaries
2. **Meaningfulness** - Must be descriptive and useful for search
3. **User Value** - Must help users find relevant visual styles
4. **Clarity** - Must be unambiguous and well-understood
5. **Style Focus** - Must relate to visual style rather than specific objects

### Filtered Out Terms

The following types of terms were excluded:

- **Object-specific terms** - man, woman, people, person, car, building, etc.
- **Generic descriptors** - image, picture, photo, artwork, design, graphic
- **Vague adjectives** - beautiful, nice, good, great, amazing, wonderful
- **Technical terms** - resolution, format, dimension, aspect, ratio
- **Pronouns and articles** - his, her, the, a, and, or, but, with
- **Numbers and identifiers** - 1, 2, 3, first, second, third
- **Common but unhelpful words** - thing, stuff, item, piece, part
- **Action-specific terms** - standing, sitting, walking, holding

## Usage Examples

### Search by Art Style

- "painting" - Find painted artwork styles
- "illustration" - Find illustrated styles
- "drawing" - Find drawn artwork styles
- "poster" - Find poster-style designs

### Search by Color

- "blue" - Find blue color schemes
- "red" - Find red color schemes
- "colorful" - Find vibrant, multi-colored styles
- "white" - Find white/minimal color schemes

### Search by Environment

- "nature" - Find natural environments
- "city" - Find urban environments
- "ocean" - Find ocean/water scenes
- "night" - Find nighttime/dark scenes

### Combined Searches

- "painting blue ocean" - Find blue painted ocean scenes
- "illustration colorful flowers" - Find colorful illustrated floral styles
- "drawing night sky" - Find drawn nighttime sky scenes
- "poster red city" - Find red poster-style city designs

## Total Statistics

- **Total curated tags**: 35
- **Original extracted tags**: 198
- **Filtered out**: 163 unhelpful/object-specific terms
- **Categories**: 4 main categories
- **Focus**: Visual style and artistic elements rather than specific objects or subjects
