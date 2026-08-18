# =====================================================================
# TAHAP 1: PEMBERSIHAN DATA (data_cleaner.py)
# =====================================================================
# Deskripsi: Membersihkan huruf berulang, spasi ganda, dan karakter rusak.
# Cara Menjalankan (dari root proyek):
#   python src/data_cleaner.py
# Output: data/processed/raw_reviews2_cleaned.csv
# =====================================================================

import os
import sys
import csv
import re

# Reconfigure stdout to UTF-8 to prevent console print errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Define relative paths based on project structure
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "raw", "raw_reviews2.csv"))
OUTPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "processed", "raw_reviews2_cleaned.csv"))

# Regex Cleaning Functions
def clean_repeated_chars(text):
    """Normalize repeated letters to maximum of 2 (e.g. enaaaaak -> enaak)"""
    if not text:
        return ""
    # Matches any letter (case-insensitive) repeated 3 or more times
    return re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', text)

def sanitize_spaces_and_lines(text):
    """Normalize excess spaces and newlines"""
    if not text:
        return ""
    # Replace carriage returns and multiple newlines with single newline
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def clean_binary_characters(text):
    """Removes non-printable binary characters, keeping standard printable characters and emojis"""
    if not text:
        return ""
    # Remove control characters except tab and newline
    return "".join(c for c in text if c.isprintable() or c in ('\n', '\t'))

def preprocess_text(text):
    """Combine all text cleaning steps"""
    text = clean_binary_characters(text)
    text = clean_repeated_chars(text)
    text = sanitize_spaces_and_lines(text)
    return text

def main():
    print("=== TAHAP 1: PEMBERSIHAN TEKS (DATA CLEANER) ===")
    print(f"Membaca data mentah dari: {INPUT_CSV}")
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Berkas input tidak ditemukan di path: {INPUT_CSV}")
        sys.exit(1)

    raw_rows = []
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    total_rows = len(raw_rows)
    print(f"Total baris dibaca: {total_rows}")

    # Prepare directories
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    cleaned_rows = []
    empty_reviews_count = 0

    for idx, row in enumerate(raw_rows):
        review_text = row.get("Review_Text", "")
        clean_text = preprocess_text(review_text)
        
        # Skip empty or whitespace-only reviews
        if not clean_text or clean_text.strip() == "":
            empty_reviews_count += 1
            continue
            
        row["Review_Text"] = clean_text
        cleaned_rows.append(row)

    print(f"Mengabaikan ulasan kosong: {empty_reviews_count} baris")
    print(f"Ulasan bersih yang siap diproses: {len(cleaned_rows)} baris")

    # Write cleaned output CSV
    fieldnames = list(raw_rows[0].keys())
    with open(OUTPUT_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"Berkas berhasil dibersihkan dan disimpan di: {OUTPUT_CSV}")
    print("Pembersihan data selesai sukses!\n")

if __name__ == "__main__":
    main()
