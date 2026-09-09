import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src.backend_engine import (
    load_clean_data,
    validate_review_dataframe,
    format_display_dataframe,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    COLUMN_DISPLAY_MAP,
    get_default_data_path
)
from dashboard.components.header import render_page_header

# Struktur kolom template CSV standar
TEMPLATE_COLUMNS = [
    'User_Name',
    'Is_Local_Guide',
    'User_Total_Reviews',
    'Rating',
    'Review_Date',
    'Has_Image',
    'Review_Text',
    'Sentiment',
    'Kategori_Operasional',
    'Urgency_Level',
    'Exact_Date'
]

# Baris contoh ulasan bersih dan valid untuk template
SAMPLE_TEMPLATE_ROWS = [
    {
        'User_Name': 'Sherryl S',
        'Is_Local_Guide': 'Ya',
        'User_Total_Reviews': 18,
        'Rating': 5,
        'Review_Date': '5 bulan lalu',
        'Has_Image': 'Ya',
        'Review_Text': 'Makanannya sangat lezat, rasa bumbu bakarnya meresap sempurna. Pelayanan ramah dan tempatnya bersih!',
        'Sentiment': 'Positif',
        'Kategori_Operasional': 'Produk/Makanan, Pelayanan/Staf',
        'Urgency_Level': 'Rendah',
        'Exact_Date': '2026-03-15'
    },
    {
        'User_Name': 'Budi Santoso',
        'Is_Local_Guide': 'Bukan',
        'User_Total_Reviews': 3,
        'Rating': 3,
        'Review_Date': '2 bulan lalu',
        'Has_Image': 'Tidak',
        'Review_Text': 'Makanannya lumayan oke untuk harga standar, tetapi antrean kasir agak panjang saat akhir pekan.',
        'Sentiment': 'Netral',
        'Kategori_Operasional': 'Harga, Pelayanan/Staf',
        'Urgency_Level': 'Rendah',
        'Exact_Date': '2026-06-10'
    },
    {
        'User_Name': 'Rina Wijaya',
        'Is_Local_Guide': 'Ya',
        'User_Total_Reviews': 9,
        'Rating': 1,
        'Review_Date': 'sebulan lalu',
        'Has_Image': 'Ya',
        'Review_Text': 'Pelayanan lambat sekali, pesanan keliru dan meja kotor. Mohon segera dievaluasi kebersihannya.',
        'Sentiment': 'Negatif',
        'Kategori_Operasional': 'Pelayanan/Staf, Suasana/Tempat',
        'Urgency_Level': 'Tinggi',
        'Exact_Date': '2026-07-22'
    }
]

@st.cache_data
def get_sample_template_csv_bytes():
    """
    Menghasilkan data byte CSV template dengan baris contoh ulasan valid.
    """
    df_template = pd.DataFrame(SAMPLE_TEMPLATE_ROWS, columns=TEMPLATE_COLUMNS)
    return df_template.to_csv(index=False).encode('utf-8')

def create_mini_sentiment_chart(pos_count, neu_count, neg_count, total_rev):
    """
    Membuat grafik batang mini untuk distribusi sentimen yang ringkas, proporsional,
    berbentuk persegi panjang vertikal yang ramping (ke atas), tidak melebar ke samping,
    jarak antar komponen rapat, dan memiliki kontras teks yang jelas terbaca.
    """
    labels = ['Positif', 'Netral', 'Negatif']
    values = [pos_count, neu_count, neg_count]
    colors = ['#22c55e', '#64748b', '#ef4444']
    
    texts = [
        f"<b>{v:,}</b><br>({v/total_rev*100:.1f}%)" if total_rev > 0 else f"{v:,}"
        for v in values
    ]
    
    max_val = max(values) if values and max(values) > 0 else 10
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        text=texts,
        textposition='outside',
        textfont=dict(color='#f8fafc', size=12, family='sans-serif'),
        cliponaxis=False,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255, 255, 255, 0.15)', width=1),
            opacity=0.95
        ),
        width=0.45,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        height=150,
        margin=dict(l=6, r=6, t=25, b=4),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=13, color='#e2e8f0', family='sans-serif'),
            showline=False
        ),
        yaxis=dict(
            range=[0, max_val * 1.35],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False
        ),
        dragmode=False
    )
    return fig

def render_upload_view():
    """
    Menampilkan antarmuka Halaman Upload & Template (Langkah 4.1):
    UI bersih dan terstruktur dengan judul ringkas maksimal 3 kata.
    """
    render_page_header(
        "📤 Upload & Template",
        "Unggah dataset ulasan baru dan unduh template data CSV standar."
    )

    tab_upload, tab_template = st.tabs([
        "⬆️ Unggah Data", 
        "⬇️ Unduh Template"
    ])

    # =========================================================
    # TAB 1: UNGGAH DATA
    # =========================================================
    with tab_upload:
        # 1. Dataset (Sebelah Kiri: Info Data Aktif, Sebelah Kanan: Unggah Berkas CSV)
        st.markdown("#### Dataset")
        active_name = st.session_state.get("active_dataset_name", "Data Bawaan Sistem")
        is_custom = st.session_state.get("is_custom_dataset", False)
        current_df = st.session_state.get("df", pd.DataFrame())
        current_rows = len(current_df) if isinstance(current_df, pd.DataFrame) else 0

        col_stat_info, col_uploader = st.columns([1, 1], gap="medium")

        with col_stat_info:
            st.markdown("<div style='font-size: 0.95rem; font-weight: 600; margin-bottom: 8px; color: #cbd5e1;'>Status Data Aktif:</div>", unsafe_allow_html=True)
            if is_custom:
                st.info(f"📂 **{active_name}** ({current_rows:,} baris)")
                if st.button("🔄 Pulihkan Data Bawaan", width="stretch", help="Kembalikan dashboard ke dataset bawaan restoran awal"):
                    default_path = get_default_data_path()
                    if default_path and os.path.exists(default_path):
                        st.session_state.df = load_clean_data(default_path)
                        st.session_state.active_dataset_name = "Data Bawaan Sistem"
                        st.session_state.is_custom_dataset = False
                        st.session_state.active_insight_index = 0
                        st.session_state.selected_tag = {"keyword": None, "category": None, "sentiment": None}
                        st.toast("Berhasil memulihkan ke dataset bawaan sistem!", icon="🔄")
                        st.rerun()
                    else:
                        st.error("Berkas dataset default tidak ditemukan di penyimpanan lokal.")
            else:
                st.success(f"📂 **Data Bawaan Sistem** ({current_rows:,} ulasan)")

        with col_uploader:
            uploaded_file = st.file_uploader(
                label="Unggah Berkas CSV:",
                type=["csv"],
                help="Hanya menerima berkas berformat .csv yang memiliki kolom-kolom wajib."
            )

            if uploaded_file is not None:
                try:
                    # Membaca data CSV mentah dari buffer unggahan
                    raw_uploaded_df = pd.read_csv(uploaded_file)
                    
                    # Validasi Skema Dataset
                    is_valid, missing_cols, found_cols = validate_review_dataframe(raw_uploaded_df)

                    if not is_valid:
                        st.error(f"❌ Validasi Gagal: `{uploaded_file.name}` tidak memenuhi kriteria kolom wajib.")
                        st.caption(f"Kolom wajib yang kurang: **{', '.join(missing_cols)}**")
                        st.warning("💡 Unduh format yang sesuai pada tab '⬇️ Unduh Template'.")
                    else:
                        # Tampilkan Status Validasi Berhasil
                        st.success(f"✅ Validasi Sukses: Seluruh kolom wajib lengkap ({len(raw_uploaded_df):,} baris).")

                        # Tombol Penerapan Data
                        if st.button("Terapkan Dataset", type="primary", width="stretch"):
                            # Pemuatan dan type-casting standar
                            cleaned_uploaded_df = load_clean_data(raw_uploaded_df)
                            
                            # Simpan ke session_state global
                            st.session_state.df = cleaned_uploaded_df
                            st.session_state.active_dataset_name = f"Unggahan: {uploaded_file.name}"
                            st.session_state.is_custom_dataset = True
                            
                            # Reset filter & wawasan agar sinkron
                            st.session_state.active_insight_index = 0
                            st.session_state.selected_tag = {"keyword": None, "category": None, "sentiment": None}
                            
                            st.toast("Dataset baru berhasil diterapkan ke dashboard!", icon="✅")
                            st.rerun()

                        # Pratinjau 5 Baris Data yang Akan Diterapkan
                        with st.expander("Pratinjau 5 Baris", expanded=False):
                            st.dataframe(format_display_dataframe(raw_uploaded_df, max_rows=5), width="stretch", hide_index=True)

                except pd.errors.EmptyDataError:
                    st.error("❌ Berkas CSV yang diunggah kosong tanpa baris data.")
                except Exception as e:
                    st.error(f"❌ Gagal membaca berkas CSV: {e}")

        # 3. Metrik Ringkasan Dataset yang Sedang Aktif
        st.divider()
        st.markdown("#### Ringkasan Dataset")

        if not current_df.empty:
            total_rev = len(current_df)
            avg_rating = current_df['Rating'].mean() if 'Rating' in current_df.columns else 0.0
            pos_count = (current_df['Sentiment'] == 'Positif').sum() if 'Sentiment' in current_df.columns else 0
            neu_count = (current_df['Sentiment'] == 'Netral').sum() if 'Sentiment' in current_df.columns else 0
            neg_count = (current_df['Sentiment'] == 'Negatif').sum() if 'Sentiment' in current_df.columns else 0

            # Ringkasan: Satu box utama (hitam) dengan box diagram batang (abu-abu) di dalamnya
            col_spacer_l, col_center_box, col_spacer_r = st.columns([1.5, 3.2, 1.5])
            
            with col_center_box:
                with st.container(border=True):
                    col_kpi, col_chart = st.columns([1.0, 1.35], gap="small")
                    with col_kpi:
                        st.markdown("<div style='padding: 6px 2px 2px 4px;'>", unsafe_allow_html=True)
                        st.metric("Total Ulasan", f"{total_rev:,}")
                        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                        st.metric("Rata-rata Rating", f"{avg_rating:.2f} ⭐" if pd.notna(avg_rating) else "N/A")
                        st.markdown("</div>", unsafe_allow_html=True)

                    with col_chart:
                        with st.container(border=True):
                            fig_sentiment = create_mini_sentiment_chart(pos_count, neu_count, neg_count, total_rev)
                            st.plotly_chart(fig_sentiment, width="stretch", config={'displayModeBar': False})

            with st.expander("Pratinjau 10 Ulasan", expanded=False):
                st.dataframe(format_display_dataframe(current_df, max_rows=10), width="stretch", hide_index=True)
        else:
            st.warning("Belum ada dataset aktif yang dimuat.")

    # =========================================================
    # TAB 2: UNDUH TEMPLATE
    # =========================================================
    with tab_template:
        st.markdown("#### Unduh Template CSV")
        st.caption("Template ulasan terstandarisasi lengkap dengan 3 baris contoh ulasan valid.")

        template_bytes = get_sample_template_csv_bytes()
        st.download_button(
            label="Unduh Berkas Template CSV",
            data=template_bytes,
            file_name="template_ulasan_kompatibel.csv",
            mime="text/csv",
            width="stretch"
        )

        st.divider()

        with st.expander("Panduan Kolom", expanded=False):
            schema_guide_data = [
                {"Kolom": "Review_Text", "Tipe Data": "Teks", "Keterangan": "Isi komentar/ulasan dari pelanggan.", "Contoh Nilai": "Makanannya sangat lezat dan bumbu meresap!"},
                {"Kolom": "Rating", "Tipe Data": "Angka (1-5)", "Keterangan": "Skor kepuasan pelanggan berupa angka murni.", "Contoh Nilai": "5 atau 4"},
                {"Kolom": "Sentiment", "Tipe Data": "Kategori", "Keterangan": "Klasifikasi sentimen (Positif, Netral, Negatif).", "Contoh Nilai": "Positif"},
                {"Kolom": "Exact_Date", "Tipe Data": "Tanggal", "Keterangan": "Format tanggal presisi ulasan YYYY-MM-DD.", "Contoh Nilai": "2026-03-15"},
                {"Kolom": "Kategori_Operasional", "Tipe Data": "Teks/Multi-label", "Keterangan": "Aspek operasional terkait (bisa multi-label dipisah koma).", "Contoh Nilai": "Produk/Makanan, Pelayanan/Staf"},
                {"Kolom": "Urgency_Level", "Tipe Data": "Kategori", "Keterangan": "Prioritas tindak lanjut (Rendah, Sedang, Tinggi).", "Contoh Nilai": "Rendah atau Tinggi"},
                {"Kolom": "User_Name", "Tipe Data": "Teks", "Keterangan": "Nama akun pengulas.", "Contoh Nilai": "Sherryl S"},
                {"Kolom": "Is_Local_Guide", "Tipe Data": "Kategori (Ya/Bukan)", "Keterangan": "Status Local Guide akun pengulas.", "Contoh Nilai": "Ya"},
                {"Kolom": "User_Total_Reviews", "Tipe Data": "Angka", "Keterangan": "Jumlah total ulasan yang pernah ditulis pengguna.", "Contoh Nilai": "18"},
                {"Kolom": "Review_Date", "Tipe Data": "Teks", "Keterangan": "Label relatif tanggal ulasan.", "Contoh Nilai": "5 bulan lalu"},
                {"Kolom": "Has_Image", "Tipe Data": "Kategori (Ya/Tidak)", "Keterangan": "Apakah ulasan menyertakan foto.", "Contoh Nilai": "Ya"}
            ]
            st.dataframe(pd.DataFrame(schema_guide_data), width="stretch", hide_index=True)

        with st.expander("Pratinjau Template", expanded=False):
            df_template_preview = pd.DataFrame(SAMPLE_TEMPLATE_ROWS, columns=TEMPLATE_COLUMNS)
            st.dataframe(format_display_dataframe(df_template_preview, max_rows=5), width="stretch", hide_index=True)
