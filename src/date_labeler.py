# =====================================================================
# TAHAP 3: PARSING TANGGAL ULASAN (date_labeler.py)
# =====================================================================
# Deskripsi: Mengonversi keterangan waktu relatif (Review_Date) dari Google
#            Maps ke tanggal absolut (format YYYY-MM-DD).
# Cara Menjalankan (dari root proyek):
#   python src/date_labeler.py
#   # Untuk menggunakan tanggal acuan khusus (misal tanggal scrape):
#   python src/date_labeler.py --ref-date 2026-08-18
# Output: data/date/raw_reviews2_dated.csv
# =====================================================================

import os
import sys
import csv
import re
import datetime
import argparse

# Reconfigure stdout to UTF-8 to prevent console print errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Define relative paths based on project structure
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "processed", "raw_reviews2_enriched2.csv"))
OUTPUT_CSV = os.path.abspath(os.path.join(SRC_DIR, "..", "data", "date", "raw_reviews2_dated.csv"))

def parse_relative_date(relative_str, ref_date):
    """
    Mengonversi ulasan relatif Indonesia (e.g. 'sebulan lalu', '3 hari lalu')
    menjadi objek datetime.date berdasarkan ref_date (tanggal acuan).
    """
    s = relative_str.lower().strip()
    
    # 1. Hari (Days)
    if "hari" in s:
        if s.startswith("sehari"):
            num = 1
        else:
            match = re.search(r'(\d+)', s)
            num = int(match.group(1)) if match else 1
        return ref_date - datetime.timedelta(days=num)
        
    # 2. Minggu (Weeks)
    elif "minggu" in s:
        if s.startswith("seminggu"):
            num = 1
        else:
            match = re.search(r'(\d+)', s)
            num = int(match.group(1)) if match else 1
        return ref_date - datetime.timedelta(weeks=num)
        
    # 3. Bulan (Months)
    elif "bulan" in s:
        if s.startswith("sebulan"):
            num = 1
        else:
            match = re.search(r'(\d+)', s)
            num = int(match.group(1)) if match else 1
            
        # Mengurangi bulan secara aman
        year = ref_date.year
        month = ref_date.month - num
        while month <= 0:
            month += 12
            year -= 1
        # Mengatasi luapan hari akhir bulan (e.g., Feb 30 -> Feb 28)
        max_days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day = min(ref_date.day, max_days[month - 1])
        return datetime.date(year, month, day)
        
    # 4. Tahun (Years)
    elif "tahun" in s:
        if s.startswith("setahun"):
            num = 1
        else:
            match = re.search(r'(\d+)', s)
            num = int(match.group(1)) if match else 1
            
        year = ref_date.year - num
        month = ref_date.month
        day = ref_date.day
        # Mengatasi hari kabisat Feb 29 jika tahun baru bukan tahun kabisat
        if month == 2 and day == 29:
            is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            if not is_leap:
                day = 28
        return datetime.date(year, month, day)
        
    # Jika format tidak dikenali, kembalikan tanggal acuan
    return ref_date

def main():
    parser = argparse.ArgumentParser(description="Penerjemah Tanggal Ulasan Google Maps")
    parser.add_argument("--ref-date", type=str, default=None, help="Tanggal acuan (format: YYYY-MM-DD). Default: hari ini.")
    args = parser.parse_args()

    print("=== TAHAP 3: PARSING TANGGAL ULASAN (DATE LABELER) ===")
    print(f"Membaca data dari: {INPUT_CSV}")

    # Verifikasi input file
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Berkas input tidak ditemukan di path: {INPUT_CSV}")
        print("Pastikan Anda sudah menjalankan 'ai_labeler.py' terlebih dahulu.")
        sys.exit(1)

    # Tentukan tanggal acuan
    if args.ref_date:
        try:
            ref_date = datetime.datetime.strptime(args.ref_date, "%Y-%m-%d").date()
            print(f"Menggunakan Tanggal Acuan (Custom): {ref_date}")
        except ValueError:
            print("Error: Format --ref-date tidak valid. Gunakan format YYYY-MM-DD (e.g. 2026-08-18).")
            sys.exit(1)
    else:
        ref_date = datetime.date.today()
        print(f"Menggunakan Tanggal Acuan (Hari Ini): {ref_date}")

    # Membaca berkas CSV
    rows = []
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"Total baris dibaca: {total_rows}")

    # Persiapkan folder output jika belum ada
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    # Konversi tanggal dan tambahkan kolom 'Exact_Date'
    print("Memproses kolom Review_Date...")
    for row in rows:
        relative_date_str = row.get("Review_Date", "")
        exact_date = parse_relative_date(relative_date_str, ref_date)
        row["Exact_Date"] = exact_date.strftime("%Y-%m-%d")

    # Siapkan header untuk berkas baru
    fieldnames = list(rows[0].keys())
    if "Exact_Date" not in fieldnames:
        fieldnames.append("Exact_Date")

    # Menulis ke berkas CSV baru
    print(f"Menyimpan hasil ke: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Proses pelabelan tanggal selesai sukses!\n")

if __name__ == "__main__":
    main()
