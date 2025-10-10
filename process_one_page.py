from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import cv2
import numpy as np
import pandas as pd
import os

# --- CONFIG ---
PDF_PATH = "assets/Gizakdag+-+Midjourney+V7+SREF+Collection+01+-+Texture+&+Effect.pdf"
OUTPUT_DIR = "output_test"
DPI = 300
GRID_ROWS, GRID_COLS = 2, 5
WATERMARK_REGION = (2200, 100, 2700, 400)  # adjust as needed
SREF_REGION = (1000, 3500, 2000, 3800)     # bottom center region for SREF detection
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- STEP 1: Convert only page 2 ---
pages = convert_from_path(PDF_PATH, dpi=DPI, first_page=2, last_page=2)
page = pages[0]

# --- STEP 2: Remove watermark ---
page_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
x1, y1, x2, y2 = WATERMARK_REGION
clone_region = page_cv[y1:y2, x1-300:x1]  # clone from left area
for i in range(x1, x2):
    for j in range(y1, y2):
        page_cv[j, i] = clone_region[j - y1, (i - x1) % clone_region.shape[1]]
page = Image.fromarray(cv2.cvtColor(page_cv, cv2.COLOR_BGR2RGB))

# --- STEP 3: Extract SREF code ---
sref_crop = page.crop(pdateSREF_REGION)
sref_text = pytesseract.image_to_string(sref_crop)
sref = "".join(filter(str.isdigit, sref_text)) or "1957797618"  # fallback to known SREF
print("Detected SREF:", sref)

# --- STEP 4: Split into grid ---
w, h = page.size
cell_w, cell_h = w // GRID_COLS, h // GRID_ROWS
records = []

for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        left = c * cell_w
        top = r * cell_h
        right = left + cell_w
        bottom = top + cell_h
        crop = page.crop((left, top, right, bottom))
        filename = f"{sref}_{r*GRID_COLS + c + 1:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        crop.save(filepath)
        records.append({"page": 2, "sref": sref, "filename": filename})

# --- STEP 5: Save metadata ---
pd.DataFrame(records).to_csv(os.path.join(OUTPUT_DIR, "metadata.csv"), index=False)
print("Saved 10 images + metadata in /output_test")