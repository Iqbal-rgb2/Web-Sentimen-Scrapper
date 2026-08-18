# =====================================================================
# TAHAP 2: INFERENSI PELABELAN AI (ai_labeler.py)
# =====================================================================
# Deskripsi: Melabeli Sentimen, Kategori, dan Urgensi dengan Gemini AI.
# Prasyarat: Pastikan GEMINI_API_KEY sudah diset di berkas .env root.
# Cara Menjalankan (dari root proyek):
#   python src/ai_labeler.py
#   # Untuk uji coba 5 baris pertama:
#   python src/ai_labeler.py --limit 5
# Output: data/processed/raw_reviews2_enriched.csv
# =====================================================================

import os
import sys
import csv
import json
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

# Reconfigure stdout to UTF-8 to prevent console print errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Define relative paths based on project structure
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables (from project root .env or home directory ~/.env)
root_env = os.path.abspath(os.path.join(SRC_DIR, "..", ".env"))
home_env = os.path.join(os.path.expanduser("~"), ".env")

if os.path.exists(root_env):
    load_dotenv(root_env)
elif os.path.exists(home_env):
    load_dotenv(home_env)
else:
    load_dotenv()

# Verify API key is present
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables, project root .env, or ~/.env file.")
    print("Please make sure you have saved your Gemini API Key before running this script.")
    sys.exit(1)

genai.configure(api_key=api_key)

# Configure paths relative to the script location
INPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "processed", "raw_reviews2_cleaned.csv"))
OUTPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "processed", "raw_reviews2_enriched.csv"))
CHECKPOINT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "processed", "raw_reviews2_checkpoint.csv"))

# Classification options
VALID_SENTIMENTS = ["Positif", "Netral", "Negatif"]
VALID_CATEGORIES = ["Produk/Makanan", "Pelayanan/Staf", "Suasana/Tempat", "Fasilitas/Parkir", "Harga"]
VALID_URGENCIES = ["Tinggi", "Sedang", "Rendah"]

# LLM Labeling Batch function using gemini-3.5-flash-lite
def label_reviews_batch(batch_data, model_name="gemini-3.5-flash-lite"):
    """
    Sends a batch of cleaned reviews to Gemini API and returns structured labels.
    """
    model = genai.GenerativeModel(model_name)
    
    system_prompt = f"""
    Anda adalah AI analis ulasan konsumen bahasa Indonesia yang bertugas menganalisis umpan balik restoran.
    Tugas Anda adalah melabeli setiap ulasan yang diberikan berdasarkan 3 dimensi:
    
    1. Sentiment: Klasifikasi keseluruhan sentimen teks. Harus salah satu dari: {VALID_SENTIMENTS}.
    2. Kategori_Operasional: Aspek operasional restoran yang dibahas dalam ulasan. Pilih MAKSIMAL 2 kategori paling dominan dari daftar berikut: {VALID_CATEGORIES}. Jika tidak ada aspek spesifik yang dibahas, kembalikan daftar kosong []. Jangan lakukan over-tagging.
    3. Urgency_Level: Tingkat urgensi ulasan. Harus salah satu dari: {VALID_URGENCIES}.
       - 'Tinggi': Ulasan negatif dengan masalah fatal (misal: makanan basi/kotor/ada ulat/rambut, keracunan makanan, staf sangat kasar/sara/kekerasan, kecurangan harga ekstrem).
       - 'Sedang': Keluhan operasional standar (misal: antrean panjang, pesanan salah/terlambat, suasana agak kotor/panas, porsi kurang).
       - 'Rendah': Ulasan positif secara keseluruhan, pujian, atau masukan minor tanpa keluhan kritis.
       
    Format masukan berupa array JSON berisi objek ulasan dengan format:
    [
      {{"id": "...", "text": "..."}}
    ]
    
    Format keluaran HARUS berupa array JSON yang valid dengan format persis seperti ini (tanpa markdown wrapper tambahan):
    [
      {{
        "id": "...",
        "sentiment": "Negatif",
        "categories": ["Pelayanan/Staf", "Fasilitas/Parkir"],
        "urgency": "Sedang"
      }}
    ]
    """

    user_prompt = json.dumps([{"id": item["id"], "text": item["clean_text"]} for item in batch_data])
    
    generation_config = {
        "response_mime_type": "application/json",
        "temperature": 0.1,
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                contents=[system_prompt, user_prompt],
                generation_config=generation_config
            )
            results = json.loads(response.text)
            
            result_map = {}
            for res in results:
                ref_id = str(res.get("id"))
                sentiment = res.get("sentiment", "Netral")
                categories = res.get("categories", [])
                urgency = res.get("urgency", "Rendah")
                
                # Validation and fallbacks
                if sentiment not in VALID_SENTIMENTS:
                    sentiment = "Netral"
                valid_cats = [c for c in categories if c in VALID_CATEGORIES][:2]
                if urgency not in VALID_URGENCIES:
                    urgency = "Rendah"
                    
                result_map[ref_id] = {
                    "Sentiment": sentiment,
                    "Kategori_Operasional": ", ".join(valid_cats),
                    "Urgency_Level": urgency
                }
            return result_map
            
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print("  Max retries reached. Returning default/empty labels for this batch.")
                return {str(item["id"]): {"Sentiment": "Netral", "Kategori_Operasional": "", "Urgency_Level": "Rendah"} for item in batch_data}

def main():
    parser = argparse.ArgumentParser(description="Pelabelan Ulasan Google Maps Menggunakan Gemini AI")
    parser.add_argument("--limit", type=int, default=None, help="Batasi jumlah baris yang diproses (untuk uji coba)")
    args = parser.parse_args()

    print("=== TAHAP 2: INFERENSI PELABELAN AI (AI LABELER) ===")
    print(f"Membaca data bersih dari: {INPUT_CSV}")
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Berkas input tidak ditemukan. Harap jalankan data_cleaner.py terlebih dahulu.")
        sys.exit(1)

    raw_rows = []
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Total baris dibaca: {len(raw_rows)}")
    
    if args.limit:
        raw_rows = raw_rows[:args.limit]
        print(f"Melakukan uji coba terbatas pada {args.limit} baris ulasan pertama.")

    fieldnames = list(raw_rows[0].keys())
    new_cols = ["Sentiment", "Kategori_Operasional", "Urgency_Level"]
    for col in new_cols:
        if col not in fieldnames:
            fieldnames.append(col)

    # Check for checkpoint and load completed row IDs to resume
    completed_ids = set()
    checkpoint_exists = os.path.exists(CHECKPOINT_CSV)
    
    if checkpoint_exists and not args.limit:
        print(f"Menemukan berkas checkpoint di: {CHECKPOINT_CSV}")
        with open(CHECKPOINT_CSV, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            checkpoint_rows = list(reader)
            completed_count = len(checkpoint_rows)
            print(f"Melanjutkan pemrosesan. Sudah ada {completed_count} baris yang selesai dilabeli.")
            completed_ids = set(range(completed_count))
    else:
        if not args.limit:
            print(f"Membuat berkas checkpoint baru di: {CHECKPOINT_CSV}")
            # Ensure folder exists
            os.makedirs(os.path.dirname(CHECKPOINT_CSV), exist_ok=True)
            with open(CHECKPOINT_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    prepared_data = []
    for idx, row in enumerate(raw_rows):
        if idx in completed_ids:
            continue
            
        prepared_data.append({
            "id": idx,
            "row_data": row,
            "clean_text": row.get("Review_Text", "")
        })

    total_to_process = len(prepared_data)
    print(f"Baris yang perlu diproses/dilabeli: {total_to_process}")

    if total_to_process == 0:
        print("Semua data sudah selesai diproses.")
    else:
        # Batch size
        batch_size = 15
        
        # Process in batches
        for i in range(0, total_to_process, batch_size):
            batch = prepared_data[i:i+batch_size]
            print(f"Memproses batch {i // batch_size + 1} / {int((total_to_process + batch_size - 1)/batch_size)} ({len(batch)} ulasan)...")
            
            labels_map = label_reviews_batch(batch)
            
            rows_to_write = []
            for item in batch:
                row_idx = str(item["id"])
                row = item["row_data"]
                
                labels = labels_map.get(row_idx, {"Sentiment": "Netral", "Kategori_Operasional": "", "Urgency_Level": "Rendah"})
                row["Sentiment"] = labels["Sentiment"]
                row["Kategori_Operasional"] = labels["Kategori_Operasional"]
                row["Urgency_Level"] = labels["Urgency_Level"]
                
                rows_to_write.append(row)
                
            if not args.limit:
                with open(CHECKPOINT_CSV, mode='a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerows(rows_to_write)
                # Rate limit safety delay: Sleep 4.5 seconds to respect the 15 RPM free tier limit
                time.sleep(4.5)
            else:
                print("\n=== HASIL UJI COBA (DRY RUN) ===")
                for row in rows_to_write:
                    print(f"\nUser: {row['User_Name']} | Rating: {row['Rating']}")
                    print(f"Teks: {row['Review_Text']}")
                    print(f"-> Sentiment: {row['Sentiment']}")
                    print(f"-> Kategori: {row['Kategori_Operasional']}")
                    print(f"-> Urgency: {row['Urgency_Level']}")
                print("================================\n")

    if not args.limit:
        print(f"Menyalin hasil final dari checkpoint ke: {OUTPUT_CSV}")
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        import shutil
        shutil.copy(CHECKPOINT_CSV, OUTPUT_CSV)
        print("Proses pelabelan penuh selesai sukses!")
        try:
            os.remove(CHECKPOINT_CSV)
            print("Berkas checkpoint dibersihkan.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
