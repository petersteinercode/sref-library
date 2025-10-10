# process_one_page_text_sref.py
# Requirements:
#   pip install pdf2image pillow PyPDF2 pandas
#   macOS: brew install poppler   (needed by pdf2image)

import os, re, pandas as pd
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

# --- CONFIG ---
PDF_PATH = "assets/Gizakdag+-+Midjourney+V7+SREF+Collection+01+-+Photorealism.pdf"
START_PAGE = 2                  # First page to process (1-based index)
END_PAGE = 59                   # Last page to process (1-based index)
OUTPUT_DIR = "output_test"
DPI = 300
GRID_ROWS, GRID_COLS = 2, 5     # 2 rows x 5 cols = 10 crops per page

# Optional page margins (pixels at 300 DPI) to exclude headers/footers if needed.
# Start with zeros; increase TOP/BOTTOM later if headers/footers leak into crops.
MARGINS_PX = dict(LEFT=0, TOP=0, RIGHT=0, BOTTOM=0)

# Grid positioning and sizing
GRID_OFFSET_X = 259    # Grid starts at x=259
GRID_OFFSET_Y = 259    # Grid starts at y=259
CELL_SPACING_X = 28    # 30px padding between cells horizontally
CELL_SPACING_Y = 28    # 30px padding between cells vertically
CELL_WIDTH = 1476      # Fixed cell width
CELL_HEIGHT = 2175     # Fixed cell height

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_sref_from_pdf(pdf_path: str, page_number: int) -> str:
    """Extracts --sref #### from PDF text layer (no OCR). Falls back to 'page{n}'."""
    reader = PdfReader(pdf_path)
    page_index = page_number - 1  # PyPDF2 is 0-based
    text = reader.pages[page_index].extract_text() or ""
    m = re.search(r"--sref\s+(\d+)", text, flags=re.IGNORECASE)
    return m.group(1) if m else f"page{page_number}"

def process_page(page_number):
    """Process a single page and return records for that page."""
    # 1) SREF from text layer
    sref = extract_sref_from_pdf(PDF_PATH, page_number)
    print(f"Page {page_number}: SREF {sref}")

    # 2) Render ONLY this page to an image
    img = convert_from_path(PDF_PATH, dpi=DPI, first_page=page_number, last_page=page_number)[0]
    w, h = img.size

    # 3) Apply margins to focus on the grid area (if needed)
    left = MARGINS_PX["LEFT"]
    top = MARGINS_PX["TOP"]
    right = w - MARGINS_PX["RIGHT"]
    bottom = h - MARGINS_PX["BOTTOM"]
    if left or top or right != w or bottom != h:
        img = img.crop((left, top, right, bottom))
        w, h = img.size

    # 4) Split into a fixed 2x5 grid with specific coordinates and cell dimensions
    # Use fixed cell dimensions as specified
    cell_w = CELL_WIDTH
    cell_h = CELL_HEIGHT

    records = []
    idx = 1
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # Calculate cell position with offset and spacing
            x1 = GRID_OFFSET_X + c * (cell_w + CELL_SPACING_X)
            y1 = GRID_OFFSET_Y + r * (cell_h + CELL_SPACING_Y)
            x2 = x1 + cell_w
            y2 = y1 + cell_h
            crop = img.crop((x1, y1, x2, y2))
            fname = f"{sref}_{idx:02d}.png"
            crop.save(os.path.join(OUTPUT_DIR, fname))
            records.append({"page": page_number, "sref": sref, "filename": fname, "row": r+1, "col": c+1, "x1": x1, "y1": y1, "x2": x2, "y2": y2})
            idx += 1
    
    return records

def main():
    all_records = []
    total_pages = END_PAGE - START_PAGE + 1
    
    print(f"Processing pages {START_PAGE} to {END_PAGE} ({total_pages} pages total)")
    
    for page_num in range(START_PAGE, END_PAGE + 1):
        try:
            records = process_page(page_num)
            all_records.extend(records)
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue
    
    # Write combined metadata CSV (append to existing if it exists)
    if all_records:
        metadata_path = os.path.join(OUTPUT_DIR, "metadata.csv")
        
        # Check if existing metadata file exists
        if os.path.exists(metadata_path):
            # Load existing data and append new records
            existing_df = pd.read_csv(metadata_path)
            new_df = pd.DataFrame(all_records)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(metadata_path, index=False)
            print(f"Appended {len(all_records)} new records to existing metadata.csv")
        else:
            # Create new metadata file
            pd.DataFrame(all_records).to_csv(metadata_path, index=False)
            print(f"Created new metadata.csv with {len(all_records)} records")
        
        total_images = len(all_records)
        print(f"Completed! Saved {total_images} images from {len(set(r['page'] for r in all_records))} pages to ./{OUTPUT_DIR}")
    else:
        print("No pages were successfully processed.")

if __name__ == "__main__":
    main()