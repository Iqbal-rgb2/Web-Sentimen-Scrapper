import os
import sys
import pandas as pd

# Konfigurasi stdout ke UTF-8 agar aman saat mencetak ke terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_clean_data(file_path):
    """
    Membaca dan membersihkan dataset ulasan dari file CSV lokal.
    - Mengonversi kolom Exact_Date ke format datetime Pandas
    - Mengisi nilai kosong pada Review_Text dengan placeholder
    - Memastikan tipe data Rating, Sentiment, dan Urgency_Level valid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File dataset tidak ditemukan di: {file_path}")
        
    df = pd.read_csv(file_path)
    
    # 1. Konversi Exact_Date ke datetime
    if 'Exact_Date' in df.columns:
        df['Exact_Date'] = pd.to_datetime(df['Exact_Date'], errors='coerce')
        
    # 2. Tangani missing value pada Review_Text
    if 'Review_Text' in df.columns:
        df['Review_Text'] = df['Review_Text'].fillna('Hanya memberikan rating')
        df['Review_Text'] = df['Review_Text'].apply(lambda x: 'Hanya memberikan rating' if str(x).strip() == '' else str(x))
        
    # 3. Validasi kolom penting lainnya
    if 'Rating' in df.columns:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0).astype(int)
        
    for col in ['Sentiment', 'Urgency_Level', 'Kategori_Operasional']:
        if col in df.columns:
            df[col] = df[col].fillna('Lainnya').astype(str)
            
    return df

def expand_categories(df):
    """
    Mengekspansi kolom Kategori_Operasional yang memuat multi-label koma
    (contoh: 'Harga, Pelayanan/Staf') menjadi baris-baris terpisah dengan kolom 'Kategori_Tunggal'.
    Digunakan untuk agregasi dan visualisasi chart aspek operasional yang akurat.
    """
    if 'Kategori_Operasional' not in df.columns:
        df_copy = df.copy()
        df_copy['Kategori_Tunggal'] = 'Lainnya'
        return df_copy
        
    df_expanded = df.copy()
    # Pecah string berpemisah koma menjadi list, lalu lakukan explode
    df_expanded['Kategori_Tunggal'] = df_expanded['Kategori_Operasional'].apply(
        lambda x: [cat.strip() for cat in str(x).split(',') if cat.strip()] if pd.notna(x) and str(x).strip() else ['Lainnya']
    )
    df_expanded = df_expanded.explode('Kategori_Tunggal')
    df_expanded['Kategori_Tunggal'] = df_expanded['Kategori_Tunggal'].fillna('Lainnya')
    
    return df_expanded

def segment_user_activity(df):
    """
    Mengelompokkan pengulas berdasarkan total ulasan akun (User_Total_Reviews)
    ke dalam 3 segmen:
    - 'User Baru (1-5)': 1 s.d. 5 ulasan
    - 'User Aktif (6-20)': 6 s.d. 20 ulasan
    - 'Top Reviewer (>20)': lebih dari 20 ulasan
    """
    df_segmented = df.copy()
    
    if 'User_Total_Reviews' not in df_segmented.columns:
        df_segmented['User_Segment'] = 'User Baru (1-5)'
        return df_segmented
        
    # Konversi kolom User_Total_Reviews ke numerik
    reviews_num = pd.to_numeric(df_segmented['User_Total_Reviews'], errors='coerce').fillna(1)
    
    conditions = [
        (reviews_num <= 5),
        (reviews_num > 5) & (reviews_num <= 20),
        (reviews_num > 20)
    ]
    choices = [
        'User Baru (1-5)',
        'User Aktif (6-20)',
        'Top Reviewer (>20)'
    ]
    
    import numpy as np
    df_segmented['User_Segment'] = np.select(conditions, choices, default='User Baru (1-5)')
    
    return df_segmented
