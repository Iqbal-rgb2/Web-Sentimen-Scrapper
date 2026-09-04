import os
import sys
import re
from collections import Counter
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
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Berkas data tidak ditemukan di path: {file_path}")
        
    df = pd.read_csv(file_path)
    
    # 1. Konversi Tanggal Eksak ke datetime
    if 'Exact_Date' in df.columns:
        df['Exact_Date'] = pd.to_datetime(df['Exact_Date'], errors='coerce')
        
    # 2. Konversi Rating ke tipe numerik murni
    if 'Rating' in df.columns:
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        
    # 3. Normalisasi Sentimen (Menghilangkan spasi luar dan menyeragamkan huruf kapital)
    if 'Sentiment' in df.columns:
        df['Sentiment'] = df['Sentiment'].astype(str).str.strip()
        df['Sentiment'] = df['Sentiment'].replace({'nan': 'Netral', '': 'Netral'})
        df['Sentiment'] = df['Sentiment'].replace({
            'positif': 'Positif', 
            'netral': 'Netral', 
            'negatif': 'Negatif'
        })
    else:
        df['Sentiment'] = 'Netral'
        
    # 4. Penanganan ulasan kosong yang hanya memberi rating tanpa komentar
    if 'Review_Text' in df.columns:
        df['Review_Text'] = df['Review_Text'].fillna('')
        df.loc[df['Review_Text'].str.strip() == '', 'Review_Text'] = 'Hanya memberikan rating'
    else:
        df['Review_Text'] = 'Hanya memberikan rating'
        
    # 5. Mengisi nilai default (NaN Handling) untuk kolom lainnya
    if 'Urgency_Level' in df.columns:
        df['Urgency_Level'] = df['Urgency_Level'].fillna('Rendah')
    else:
        df['Urgency_Level'] = 'Rendah'
        
    if 'Kategori_Operasional' in df.columns:
        df['Kategori_Operasional'] = df['Kategori_Operasional'].fillna('')
    else:
        df['Kategori_Operasional'] = ''
        
    if 'Is_Local_Guide' in df.columns:
        df['Is_Local_Guide'] = df['Is_Local_Guide'].fillna('Bukan')
    else:
        df['Is_Local_Guide'] = 'Bukan'
        
    if 'Has_Image' in df.columns:
        df['Has_Image'] = df['Has_Image'].fillna('Tidak')
    else:
        df['Has_Image'] = 'Tidak'
        
    return df

def expand_categories(df):
    """
    Memisahkan baris yang memiliki beberapa kategori operasional (multi-label)
    menjadi baris-baris terpisah (kategori tunggal) untuk analisis statistik & grafik.
    """
    if df.empty or 'Kategori_Operasional' not in df.columns:
        new_df = df.copy()
        new_df['Kategori_Tunggal'] = ''
        return new_df
        
    rows = []
    for _, row in df.iterrows():
        cats = row['Kategori_Operasional']
        if not cats or pd.isna(cats) or str(cats).strip() == '' or str(cats).lower() == 'nan':
            continue
            
        # Pisahkan kategori berbasis koma (e.g. "Harga, Pelayanan/Staf" -> ["Harga", "Pelayanan/Staf"])
        split_cats = [c.strip() for c in str(cats).split(',')]
        for cat in split_cats:
            if cat:
                new_row = row.copy()
                new_row['Kategori_Tunggal'] = cat
                rows.append(new_row)
                
    if not rows:
        new_df = df.copy()
        new_df['Kategori_Tunggal'] = ''
        return new_df
        
    return pd.DataFrame(rows)

def segment_user_activity(df):
    """
    Mengelompokkan ulasan berdasarkan jumlah riwayat ulasan akun (User_Total_Reviews).
    Kategori segmen:
    - User Baru (1-5 ulasan)
    - User Aktif (6-20 ulasan)
    - Top Reviewer (>20 ulasan)
    """
    df_copy = df.copy()
    if 'User_Total_Reviews' not in df_copy.columns:
        df_copy['User_Segment'] = 'User Baru (1-5)'
        return df_copy
        
    # Bersihkan dan konversi total ulasan ke numerik
    total_reviews = df_copy['User_Total_Reviews'].astype(str).str.replace(r'[.,]', '', regex=True)
    total_reviews = pd.to_numeric(total_reviews, errors='coerce').fillna(0)
    
    # Menentukan segmen keaktifan
    def get_segment(count):
        if count <= 5:
            return 'User Baru (1-5)'
        elif count <= 20:
            return 'User Aktif (6-20)'
        else:
            return 'Top Reviewer (>20)'
            
    df_copy['User_Segment'] = total_reviews.apply(get_segment)
    return df_copy

def get_clean_snippet(text, max_len=140):
    """
    Membersihkan teks ulasan dari newline berlebih, karakter emoji liar,
    dan memotongnya agar rapi saat disematkan sebagai kutipan contoh ulasan.
    """
    if not text or pd.isna(text):
        return "Pelayanan memuaskan dan makanan lezat."
    s = str(text).replace('\r\n', ' ').replace('\n', ' ').strip()
    s = " ".join(s.split())
    # Hapus karakter emoji liar agar aman dicetak di semua jenis konsol Windows
    s = s.encode('ascii', 'ignore').decode('ascii')
    if len(s) > max_len:
        return s[:max_len].rstrip() + "..."
    return s

def calculate_10_insights(df):
    """
    Menghitung 10 Wawasan Operasional (10 Insights) yang ramah, relevan untuk bisnis restoran,
    dan bebas istilah teknis, dilengkapi data angka riil serta contoh kutipan ulasan konkret.
    Mengembalikan dictionary {1: {"title": ..., "text": ...}, ... 10: {...}}
    """
    if df.empty:
        return {
            i: {
                "title": f"Wawasan {i}",
                "text": "Data ulasan tidak tersedia atau belum dimuat."
            } for i in range(1, 11)
        }
        
    total_ulasan = len(df)
    
    # --- Perhitungan Dasar Sentimen ---
    df_pos = df[df['Sentiment'] == 'Positif']
    df_net = df[df['Sentiment'] == 'Netral']
    df_neg = df[df['Sentiment'] == 'Negatif']
    
    jumlah_positif = len(df_pos)
    jumlah_netral = len(df_net)
    jumlah_negatif = len(df_neg)
    
    persen_positif = round((jumlah_positif / total_ulasan) * 100, 1) if total_ulasan > 0 else 0.0
    persen_netral = round((jumlah_netral / total_ulasan) * 100, 1) if total_ulasan > 0 else 0.0
    persen_negatif = round((jumlah_negatif / total_ulasan) * 100, 1) if total_ulasan > 0 else 0.0
    
    sentiment_series = df['Sentiment'].dropna()
    sentiment_dominan = sentiment_series.mode()[0] if not sentiment_series.empty else 'Netral'
    jumlah_sentimen_dominan = sentiment_series.value_counts().max() if not sentiment_series.empty else 0
    persentase_sentimen_dominan = round((jumlah_sentimen_dominan / total_ulasan) * 100, 1) if total_ulasan > 0 else 0.0
    
    if sentiment_dominan == 'Negatif':
        kepuasan_umum = "kurang puas (didominasi keluhan)"
        df_dom = df_neg
    elif sentiment_dominan == 'Positif':
        kepuasan_umum = "sangat puas (didominasi pujian)"
        df_dom = df_pos
    else:
        kepuasan_umum = "merasa biasa saja (netral)"
        df_dom = df_net
        
    contoh_ulasan_dominan = get_clean_snippet(df_dom['Review_Text'].iloc[0] if not df_dom.empty else "")
    
    # 1. Kepuasan Pelanggan Secara Umum
    insight_1 = (
        f"Dari total **{total_ulasan} ulasan** yang masuk, sebagian besar pelanggan merasa **{kepuasan_umum}** "
        f"dengan jumlah **{jumlah_sentimen_dominan} ulasan ({persentase_sentimen_dominan}%)**. Sementara itu, "
        f"ada **{jumlah_positif} ulasan** yang merasa puas dan **{jumlah_netral} ulasan** yang merasa biasa saja. "
        f"Contoh tanggapan pelanggan yang paling menggambarkan hal ini: *\"{contoh_ulasan_dominan}\"*."
    )
    
    # --- Analisis Keluhan Negatif ---
    neg_cats_series = pd.Series(dtype=str)
    if not df_neg.empty and 'Kategori_Operasional' in df_neg.columns:
        neg_cats_series = df_neg['Kategori_Operasional'].astype(str).str.split(',').explode().str.strip()
        neg_cats_series = neg_cats_series[~neg_cats_series.str.lower().isin(['', 'nan', 'none'])]
        
    cat_neg_vc = neg_cats_series.value_counts() if not neg_cats_series.empty else pd.Series(dtype=int)
    total_komplain_negatif = cat_neg_vc.sum() if not cat_neg_vc.empty else 0
    
    # 2. Masalah Utama yang Sering Dikeluhkan (Keluhan #1)
    if not cat_neg_vc.empty:
        kategori_masalah_terbanyak = cat_neg_vc.index[0]
        jumlah_kategori_terbanyak = cat_neg_vc.iloc[0]
        persen_keluhan = round((jumlah_kategori_terbanyak / total_komplain_negatif) * 100, 1) if total_komplain_negatif > 0 else 0.0
        
        matched_neg = df_neg[df_neg['Kategori_Operasional'].astype(str).str.contains(kategori_masalah_terbanyak, case=False, na=False)]
        contoh_ulasan_komplain = get_clean_snippet(matched_neg['Review_Text'].iloc[0] if not matched_neg.empty else (df_neg['Review_Text'].iloc[0] if not df_neg.empty else ""))
    else:
        kategori_masalah_terbanyak = "Pelayanan"
        jumlah_kategori_terbanyak = 0
        persen_keluhan = 0.0
        contoh_ulasan_komplain = "Belum ada keluhan spesifik yang tercatat."
        
    insight_2 = (
        f"Hal yang paling sering dikeluhkan pelanggan adalah seputar **{kategori_masalah_terbanyak}**, "
        f"dengan total **{jumlah_kategori_terbanyak} keluhan ({persen_keluhan}%)** dari seluruh komplain yang ada. "
        f"Bagian ini perlu segera dicek dan diperbaiki agar pelanggan tidak kecewa. "
        f"Contoh keluhan pelanggan: *\"{contoh_ulasan_komplain}\"*."
    )
    
    # 3. Masalah Mendesak yang Harus Segera Ditangani (Urgensi Tinggi)
    df_tinggi = df[df['Urgency_Level'] == 'Tinggi']
    jumlah_urgensi_tinggi = len(df_tinggi)
    if not df_tinggi.empty and 'Kategori_Operasional' in df_tinggi.columns:
        tinggi_cats = df_tinggi['Kategori_Operasional'].astype(str).str.split(',').explode().str.strip()
        tinggi_cats = tinggi_cats[~tinggi_cats.str.lower().isin(['', 'nan', 'none'])]
        kategori_kritis_dominan = tinggi_cats.mode()[0] if not tinggi_cats.empty else "layanan utama"
        contoh_ulasan_kritis = get_clean_snippet(df_tinggi['Review_Text'].iloc[0])
    else:
        kategori_kritis_dominan = "operasional harian"
        contoh_ulasan_kritis = "Saat ini tidak ada keluhan dengan urgensi tinggi."
        
    insight_3 = (
        f"Ada **{jumlah_urgensi_tinggi} ulasan** dengan keluhan cukup parah dan mendesak untuk segera ditangani "
        f"oleh pihak restoran, terutama terkait masalah **{kategori_kritis_dominan}**. Jika dibiarkan, hal ini bisa "
        f"membuat pelanggan kapok untuk datang lagi. Contoh keluhan mendesak tersebut: *\"{contoh_ulasan_kritis}\"*."
    )
    
    # 4. Masalah Lain yang Juga Perlu Diperhatikan (Keluhan #2)
    if len(cat_neg_vc) >= 2:
        kategori_masalah_sekunder = cat_neg_vc.index[1]
        jumlah_kategori_sekunder = cat_neg_vc.iloc[1]
        matched_sekunder = df_neg[df_neg['Kategori_Operasional'].astype(str).str.contains(kategori_masalah_sekunder, case=False, na=False)]
        contoh_ulasan_sekunder = get_clean_snippet(matched_sekunder['Review_Text'].iloc[0] if not matched_sekunder.empty else "")
    else:
        kategori_masalah_sekunder = "Fasilitas/Suasana"
        jumlah_kategori_sekunder = 0
        contoh_ulasan_sekunder = "Tidak ada masalah sekunder yang menonjol."
        
    insight_4 = (
        f"Selain masalah utama di atas, pelanggan juga cukup banyak mengeluhkan hal terkait **{kategori_masalah_sekunder}**, "
        f"yaitu sebanyak **{jumlah_kategori_sekunder} keluhan**. Hal ini juga perlu diawasi agar tidak menjadi "
        f"masalah yang makin besar. Contoh keluhannya: *\"{contoh_ulasan_sekunder}\"*."
    )
    
    # 5. Hal yang Paling Jarang Dikeluhkan Pelanggan (Paling Aman)
    standard_categories = ['Produk/Makanan', 'Pelayanan/Staf', 'Suasana/Tempat', 'Fasilitas/Parkir', 'Harga']
    cat_neg_counts = {cat: (cat_neg_vc.get(cat, 0)) for cat in standard_categories}
    kategori_minim_keluhan = min(cat_neg_counts, key=cat_neg_counts.get)
    jumlah_keluhan_minim = cat_neg_counts[kategori_minim_keluhan]
    
    matched_pos_minim = df_pos[df_pos['Kategori_Operasional'].astype(str).str.contains(kategori_minim_keluhan, case=False, na=False)]
    if not matched_pos_minim.empty:
        contoh_ulasan_minim_keluhan = get_clean_snippet(matched_pos_minim['Review_Text'].iloc[0])
    else:
        contoh_ulasan_minim_keluhan = get_clean_snippet(df['Review_Text'].iloc[0] if not df.empty else "")
        
    insight_5 = (
        f"Pelayanan di bagian **{kategori_minim_keluhan}** dinilai paling aman dan jarang bermasalah, "
        f"karena hanya menerima **{jumlah_keluhan_minim} keluhan** dari seluruh pelanggan. Kualitas di bagian "
        f"ini sudah cukup bagus dan perlu terus dijaga. Contoh komentar pelanggan: *\"{contoh_ulasan_minim_keluhan}\"*."
    )
    
    # 6. Skor Kesehatan Pelayanan Restoran
    rating_clean = pd.to_numeric(df['Rating'], errors='coerce').dropna()
    rating_rata = round(rating_clean.mean(), 2) if not rating_clean.empty else 0.0
    
    sub_pos = (jumlah_positif / total_ulasan) * 50 if total_ulasan > 0 else 0
    sub_rat = (rating_rata / 5.0) * 30
    sub_urg = (1.0 - (jumlah_urgensi_tinggi / total_ulasan)) * 20 if total_ulasan > 0 else 20
    skor_kesehatan = int(round(sub_pos + sub_rat + sub_urg))
    skor_kesehatan = max(0, min(100, skor_kesehatan))
    
    if skor_kesehatan >= 75:
        status_kesehatan = "Sangat Baik"
    elif skor_kesehatan >= 50:
        status_kesehatan = "Cukup Baik"
    else:
        status_kesehatan = "Perlu Perhatian Khusus"
        
    contoh_ulasan_kesehatan = get_clean_snippet(df_pos['Review_Text'].iloc[0] if not df_pos.empty else (df_net['Review_Text'].iloc[0] if not df_net.empty else df_neg['Review_Text'].iloc[0]))
    
    insight_6 = (
        f"Kondisi pelayanan restoran secara keseluruhan dinilai berada dalam status **{status_kesehatan}** "
        f"dengan nilai **{skor_kesehatan} dari 100**, melihat perbandingan antara **{jumlah_positif} orang puas** "
        f"dan **{jumlah_negatif} orang mengeluh**. Ini menunjukkan gambaran seberapa nyaman pelanggan makan di sini. "
        f"Contoh ulasannya: *\"{contoh_ulasan_kesehatan}\"*."
    )
    
    # 7. Bintang Rating yang Paling Sering Diberikan
    if not rating_clean.empty:
        rating_terbanyak = int(rating_clean.mode()[0])
        jumlah_rating_terbanyak = rating_clean.value_counts().max()
    else:
        rating_terbanyak = 0
        jumlah_rating_terbanyak = 0
        
    jumlah_bintang_1 = len(df[df['Rating'] == 1])
    jumlah_bintang_5 = len(df[df['Rating'] == 5])
    
    df_star1 = df[df['Rating'] == 1]
    contoh_ulasan_bintang_1 = get_clean_snippet(df_star1['Review_Text'].iloc[0] if not df_star1.empty else "Belum ada ulasan bintang 1.")
    
    insight_7 = (
        f"Rata-rata nilai yang diberikan pelanggan adalah **{rating_rata} dari 5 bintang**, dan nilai yang paling "
        f"sering didapat adalah **bintang {rating_terbanyak}** (diberikan oleh **{jumlah_rating_terbanyak} pelanggan**). "
        f"Sebagai perbandingan, ada **{jumlah_bintang_1} pelanggan** memberi bintang 1 dan **{jumlah_bintang_5} pelanggan** "
        f"memberi bintang 5. Contoh kekecewaan pelanggan bintang 1: *\"{contoh_ulasan_bintang_1}\"*."
    )
    
    # 8. Hal yang Paling Disukai dan Dipuji Pelanggan
    pos_cats_series = pd.Series(dtype=str)
    if not df_pos.empty and 'Kategori_Operasional' in df_pos.columns:
        pos_cats_series = df_pos['Kategori_Operasional'].astype(str).str.split(',').explode().str.strip()
        pos_cats_series = pos_cats_series[~pos_cats_series.str.lower().isin(['', 'nan', 'none'])]
        
    cat_pos_vc = pos_cats_series.value_counts() if not pos_cats_series.empty else pd.Series(dtype=int)
    if not cat_pos_vc.empty:
        kategori_positif_terbanyak = cat_pos_vc.index[0]
        jumlah_kategori_positif = cat_pos_vc.iloc[0]
        persen_pujian_pos = round((jumlah_kategori_positif / len(df_pos)) * 100, 1) if len(df_pos) > 0 else 0.0
        matched_pos = df_pos[df_pos['Kategori_Operasional'].astype(str).str.contains(kategori_positif_terbanyak, case=False, na=False)]
        contoh_ulasan_positif = get_clean_snippet(matched_pos['Review_Text'].iloc[0] if not matched_pos.empty else df_pos['Review_Text'].iloc[0])
    else:
        kategori_positif_terbanyak = "Produk/Makanan"
        jumlah_kategori_positif = len(df_pos)
        persen_pujian_pos = 100.0 if len(df_pos) > 0 else 0.0
        contoh_ulasan_positif = get_clean_snippet(df_pos['Review_Text'].iloc[0] if not df_pos.empty else "Rasa makanannya enak.")
        
    insight_8 = (
        f"Hal yang paling banyak disukai dan dipuji pelanggan adalah seputar **{kategori_positif_terbanyak}**, "
        f"dengan total **{jumlah_kategori_positif} pujian ({persen_pujian_pos}%)** dari ulasan positif. Kelebihan ini "
        f"adalah daya tarik utama restoran yang harus terus dipertahankan. Contoh pujian dari pelanggan: *\"{contoh_ulasan_positif}\"*."
    )
    
    # 9. Waktu dan Hari yang Paling Ramai Ulasan
    df_dated = df.dropna(subset=['Exact_Date']).copy()
    if not df_dated.empty and pd.api.types.is_datetime64_any_dtype(df_dated['Exact_Date']):
        hari_map = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
        }
        df_dated['Nama_Hari'] = df_dated['Exact_Date'].dt.day_name().map(hari_map).fillna('Sabtu')
        hari_vc = df_dated['Nama_Hari'].value_counts()
        hari_terpadat = hari_vc.index[0] if not hari_vc.empty else "Sabtu"
        jumlah_hari_terpadat = hari_vc.iloc[0] if not hari_vc.empty else 0
        
        jumlah_weekend = df_dated['Nama_Hari'].isin(['Sabtu', 'Minggu']).sum()
        persen_weekend = round((jumlah_weekend / len(df_dated)) * 100, 1)
        
        matched_hari = df_dated[df_dated['Nama_Hari'] == hari_terpadat]
        contoh_ulasan_hari = get_clean_snippet(matched_hari['Review_Text'].iloc[0] if not matched_hari.empty else "")
    else:
        hari_terpadat = "Akhir Pekan"
        jumlah_hari_terpadat = total_ulasan
        persen_weekend = 50.0
        contoh_ulasan_hari = get_clean_snippet(df['Review_Text'].iloc[0] if not df.empty else "")
        
    insight_9 = (
        f"Pelanggan paling aktif memberikan ulasan pada hari **{hari_terpadat}** (mencapai **{jumlah_hari_terpadat} ulasan**), "
        f"dengan **{persen_weekend}% ulasan** masuk di akhir pekan (Sabtu & Minggu). Hari-hari ramai seperti ini butuh "
        f"kesiapan staf lebih ekstra agar pelayanan tetap lancar. Contoh ulasan di hari ramai: *\"{contoh_ulasan_hari}\"*."
    )
    
    # 10. Ulasan dan Masalah Terbaru yang Baru Masuk
    if not df_dated.empty:
        df_sorted_latest = df_dated.sort_values(by='Exact_Date', ascending=False)
        row_latest = df_sorted_latest.iloc[0]
        exact_date_terbaru = row_latest['Exact_Date'].strftime('%d %B %Y') if hasattr(row_latest['Exact_Date'], 'strftime') else str(row_latest['Exact_Date'])
        rating_terbaru = row_latest.get('Rating', 'N/A')
        sentiment_terbaru = row_latest.get('Sentiment', 'Netral')
        kategori_terbaru = row_latest.get('Kategori_Operasional', 'pelayanan')
        if not kategori_terbaru or str(kategori_terbaru).lower() == 'nan':
            kategori_terbaru = 'pelayanan umum'
        contoh_ulasan_terbaru = get_clean_snippet(row_latest.get('Review_Text', ''))
    else:
        exact_date_terbaru = "hari ini"
        rating_terbaru = "5"
        sentiment_terbaru = "Positif"
        kategori_terbaru = "layanan"
        contoh_ulasan_terbaru = get_clean_snippet(df['Review_Text'].iloc[0] if not df.empty else "")
        
    insight_10 = (
        f"Ulasan paling baru yang masuk ke sistem tercatat pada tanggal **{exact_date_terbaru}**, di mana pelanggan "
        f"memberikan nilai **{rating_terbaru} bintang ({sentiment_terbaru})** mengenai hal terkait **{kategori_terbaru}**. "
        f"Catatan terbaru ini bisa langsung dicek bersama tim yang bertugas hari ini: *\"{contoh_ulasan_terbaru}\"*."
    )
    
    insights = {
        1: {"title": "Kepuasan Pelanggan Secara Umum", "text": insight_1},
        2: {"title": "Masalah Utama yang Sering Dikeluhkan", "text": insight_2},
        3: {"title": "Masalah Mendesak yang Harus Segera Ditangani", "text": insight_3},
        4: {"title": "Masalah Lain yang Juga Perlu Diperhatikan", "text": insight_4},
        5: {"title": "Hal yang Paling Jarang Dikeluhkan Pelanggan", "text": insight_5},
        6: {"title": "Skor Kesehatan Pelayanan Restoran", "text": insight_6},
        7: {"title": "Bintang Rating yang Paling Sering Diberikan", "text": insight_7},
        8: {"title": "Hal yang Paling Disukai dan Dipuji Pelanggan", "text": insight_8},
        9: {"title": "Waktu dan Hari yang Paling Ramai Ulasan", "text": insight_9},
        10: {"title": "Ulasan dan Masalah Terbaru yang Baru Masuk", "text": insight_10}
    }
    return insights

# Daftar Stopwords Bahasa Indonesia untuk Penyaringan Kata Kunci Ulasan
INDONESIAN_STOPWORDS = {
    'yang', 'di', 'ke', 'dari', 'dan', 'atau', 'ini', 'itu', 'untuk', 'pada',
    'dengan', 'adalah', 'yaitu', 'yakni', 'seperti', 'sebagai', 'oleh', 'karena',
    'maka', 'sehingga', 'jika', 'bila', 'kalau', 'kalo', 'tetapi', 'tapi',
    'namun', 'melainkan', 'hanya', 'memberikan', 'rating', 'saya', 'aku',
    'kami', 'kita', 'anda', 'mereka', 'dia', 'beliau', 'nya', 'ada', 'tidak',
    'bukan', 'jangan', 'belum', 'tak', 'gak', 'nggak', 'ngga', 'ga', 'bgt',
    'banget', 'sangat', 'amat', 'sekali', 'agak', 'kurang', 'lebih', 'paling',
    'bisa', 'dapat', 'akan', 'telah', 'sudah', 'udah', 'sdh', 'sedang',
    'masih', 'pernah', 'selalu', 'sering', 'kadang', 'biasa', 'hanya', 'cuma',
    'aja', 'saja', 'juga', 'jg', 'pun', 'pula', 'serta', 'lagi', 'lg', 'lalu',
    'kemudian', 'setelah', 'sebelum', 'saat', 'ketika', 'waktu', 'pas',
    'tempat', 'makan', 'disini', 'sini', 'situ', 'sana', 'sama', 'dgn',
    'dg', 'jd', 'jadi', 'buat', 'utk', 'kpd', 'kepada', 'terhadap',
    'tentang', 'mengenai', 'sih', 'deh', 'dong', 'kok', 'loh',
    'lah', 'kah', 'nih', 'tuh', 'yuk', 'kan', 'ya', 'yah',
    'banyak', 'beberapa', 'semua', 'seluruh', 'tiap', 'setiap', 'lain',
    'lainnya', 'begitu', 'begini', 'kenapa', 'mengapa', 'bagaimana',
    'gimana', 'mana', 'siapa', 'apa', 'kapan', 'mau', 'ingin', 'hendak',
    'bikin', 'terus', 'cukup', 'tetap', 'malah', 'justru',
    'bahkan', 'mesti', 'harus', 'wajib', 'boleh', 'pasti', 'tentu',
    'kali', 'hari', 'malam', 'siang', 'pagi', 'sore', 'jam', 'menit',
    'resto', 'rumah', 'restoran', 'warung', 'menu', 'pesan', 'order'
}

# Kamus Kata Sifat / Opini Sentimen Berdasarkan 5 Kategori Operasional Restoran
