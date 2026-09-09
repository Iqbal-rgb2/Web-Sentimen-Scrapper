import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.backend_engine import expand_categories, get_clean_snippet
from dashboard.components.header import render_page_header

def calculate_kpi_metrics(df):
    """
    Menghitung 4 metrik KPI utama untuk baris ringkasan eksekutif:
    1. Total Ulasan
    2. Rata-rata Rating Bintang
    3. Rasio Positif (%)
    4. Jumlah Kasus Urgensi Tinggi
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "total_ulasan": 0,
            "rating_rata": 0.0,
            "rasio_positif": 0.0,
            "urgensi_tinggi": 0
        }

    total = len(df)

    # 1. Rata-rata Rating
    if "Rating" in df.columns:
        rating_num = pd.to_numeric(df["Rating"], errors="coerce")
        rating_rata = float(rating_num.mean()) if not rating_num.dropna().empty else 0.0
    else:
        rating_rata = 0.0

    # 2. Rasio Positif
    if "Sentiment" in df.columns:
        pos_count = int((df["Sentiment"].astype(str).str.strip().str.capitalize() == "Positif").sum())
        rasio_positif = (pos_count / total) * 100.0 if total > 0 else 0.0
    else:
        rasio_positif = 0.0

    # 3. Kasus Urgensi Tinggi
    if "Urgency_Level" in df.columns:
        urgensi_tinggi = int((df["Urgency_Level"].astype(str).str.strip().str.capitalize() == "Tinggi").sum())
    else:
        urgensi_tinggi = 0

    return {
        "total_ulasan": total,
        "rating_rata": rating_rata,
        "rasio_positif": rasio_positif,
        "urgensi_tinggi": urgensi_tinggi
    }

def render_kpi_row(kpi_data):
    """
    Merender baris 4 kartu ringkasan KPI di bagian atas dashboard dengan tata letak 4 kolom.
    """
    col1, col2, col3, col4 = st.columns(4)

    cards = [
        {
            "col": col1,
            "label": "Total Ulasan",
            "value": f"{kpi_data['total_ulasan']:,}",
            "color": "#f8fafc",
            "caption": "Akumulasi seluruh ulasan pelanggan aktif."
        },
        {
            "col": col2,
            "label": "Rata-rata Rating",
            "value": f"{kpi_data['rating_rata']:.2f} ⭐",
            "color": "#f8fafc",
            "caption": "Skor rata-rata kepuasan dari skala 5.0."
        },
        {
            "col": col3,
            "label": "Rasio Positif",
            "value": f"{kpi_data['rasio_positif']:.1f}%",
            "color": "#f8fafc",
            "caption": "Proporsi ulasan dengan sentimen puas."
        },
        {
            "col": col4,
            "label": "Kasus Urgensi Tinggi",
            "value": f"{kpi_data['urgensi_tinggi']:,}",
            "color": "#ef4444",
            "caption": "Keluhan kritis prioritas operasional."
        }
    ]

    for c in cards:
        with c["col"]:
            st.html(f"""
            <div class="kpi-metric-card">
                <div>
                    <div class="kpi-label">{c['label']}</div>
                    <div class="kpi-value" style="color: {c['color']};">{c['value']}</div>
                </div>
                <div class="kpi-caption">{c['caption']}</div>
            </div>
            """)

def create_donut_chart(df, variable_name):
    """
    Membangun objek Plotly Donut Chart untuk 3 pilihan variabel:
    1. Distribusi Sentimen
    2. Tingkat Urgensi
    3. Ulasan Bergambar
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text="Data tidak tersedia", showarrow=False, font=dict(color="#94a3b8", size=14))]
        )
        return fig

    if variable_name == "Distribusi Sentimen":
        order = ["Positif", "Netral", "Negatif"]
        color_map = {"Positif": "#22c55e", "Netral": "#64748b", "Negatif": "#ef4444"}
        col_series = df["Sentiment"].astype(str).str.strip().str.capitalize()
        counts = {cat: int((col_series == cat).sum()) for cat in order}
        labels = order
        values = [counts[c] for c in order]
        colors = [color_map[c] for c in order]

    elif variable_name == "Tingkat Urgensi":
        order = ["Tinggi", "Sedang", "Rendah"]
        color_map = {"Tinggi": "#ef4444", "Sedang": "#f59e0b", "Rendah": "#3b82f6"}
        col_series = df["Urgency_Level"].astype(str).str.strip().str.capitalize()
        counts = {cat: int((col_series == cat).sum()) for cat in order}
        labels = order
        values = [counts[c] for c in order]
        colors = [color_map[c] for c in order]

    else:  # Ulasan Bergambar
        order = ["Ada Foto", "Tanpa Foto"]
        color_map = {"Ada Foto": "#3b82f6", "Tanpa Foto": "#64748b"}
        col_series = df["Has_Image"].astype(str).str.strip().str.capitalize()
        ada_foto = int((col_series == "Ya").sum())
        tanpa_foto = len(df) - ada_foto
        labels = order
        values = [ada_foto, tanpa_foto]
        colors = [color_map[c] for c in order]

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.58,
            marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
            textinfo="percent",
            textfont=dict(size=13, color="#ffffff", family="sans-serif"),
            hovertemplate="<b>%{label}</b><br>%{value:,} ulasan (%{percent})<extra></extra>",
            sort=False
        )
    ])

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#cbd5e1")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=15, b=25, l=15, r=15),
        height=320
    )

    return fig

def create_bar_chart(df, variable_name):
    """
    Membangun objek Plotly Bar Chart bersih untuk 2 pilihan variabel:
    1. Isu Aspek Operasional
    2. Sebaran Rating Bintang

    Catatan Desain Sesuai Arahan Pengguna:
    Angka nilai ulasan TIDAK ditampilkan di ujung batang, melainkan diletakkan
    di bawah judul/label kategori pada sumbu X agar diagram bersih tanpa angka bertumpuk.
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text="Data tidak tersedia", showarrow=False, font=dict(color="#94a3b8", size=14))]
        )
        return fig

    if variable_name == "Isu Aspek Operasional":
        exp_df = expand_categories(df)
        cat_counts = exp_df["Kategori_Tunggal"].value_counts()
        # Filter kategori kosong atau none
        cat_counts = cat_counts[~cat_counts.index.str.lower().isin(["", "nan", "none"])]

        categories = list(cat_counts.index)
        values = [int(v) for v in cat_counts.values]
        colors = ["#6366f1"] * len(categories)

        # Label sumbu X: Nama kategori di atas, angka ulasan di bawahnya
        x_ticks = [f"{cat}<br><b>{val:,} ulasan</b>" for cat, val in zip(categories, values)]

    else:  # Sebaran Rating Bintang
        rating_series = pd.to_numeric(df["Rating"], errors="coerce").dropna().astype(int)
        rating_stars = [1, 2, 3, 4, 5]
        values = [int((rating_series == star).sum()) for star in rating_stars]
        colors = ["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e"]
        categories = [f"Bintang {star}" for star in rating_stars]

        # Label sumbu X: Bintang di atas, angka ulasan di bawahnya
        x_ticks = [f"⭐ {star}<br><b>{val:,} ulasan</b>" for star, val in zip(rating_stars, values)]

    fig = go.Figure(data=[
        go.Bar(
            x=list(range(len(categories))),
            y=values,
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
            textposition="none",  # Tidak memunculkan angka di ujung batang
            hovertemplate="<b>%{customdata}</b><br>%{y:,} ulasan<extra></extra>",
            customdata=categories
        )
    ])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=15, b=20, l=20, r=20),
        height=320,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(categories))),
            ticktext=x_ticks,
            tickfont=dict(size=11, color="#cbd5e1"),
            gridcolor="rgba(255, 255, 255, 0.05)",
            linecolor="rgba(255, 255, 255, 0.15)"
        ),
        yaxis=dict(
            title=dict(text="Jumlah Ulasan", font=dict(size=12, color="#94a3b8")),
            tickfont=dict(size=11, color="#94a3b8"),
            gridcolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.12)"
        ),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12)
    )

    return fig

def generate_donut_summary(df, variable_name):
    """
    Menghasilkan narasi analisis otomatis untuk Donut Chart sesuai variabel yang dipilih.
    """
    if df is None or df.empty:
        return "Data ulasan tidak tersedia untuk analisis."

    total = len(df)

    if variable_name == "Distribusi Sentimen":
        pos_count = int((df["Sentiment"] == "Positif").sum())
        net_count = int((df["Sentiment"] == "Netral").sum())
        neg_count = int((df["Sentiment"] == "Negatif").sum())

        dom_sentiment = "Netral"
        dom_count = net_count
        if pos_count >= net_count and pos_count >= neg_count:
            dom_sentiment = "Positif"
            dom_count = pos_count
        elif neg_count >= net_count and neg_count >= pos_count:
            dom_sentiment = "Negatif"
            dom_count = neg_count

        dom_pct = (dom_count / total) * 100.0 if total > 0 else 0.0
        pos_pct = (pos_count / total) * 100.0 if total > 0 else 0.0
        neg_pct = (neg_count / total) * 100.0 if total > 0 else 0.0

        return (
            f"Berdasarkan catatan terhadap **{total:,} ulasan** pelanggan, respons konsumen didominasi oleh "
            f"ulasan bersentimen **{dom_sentiment}** sebanyak **{dom_count:,} ulasan ({dom_pct:.1f}%)**. "
            f"Secara umum, tingkat kepuasan pelanggan mencatat **{pos_pct:.1f}% ulasan positif** berbanding "
            f"**{neg_pct:.1f}% keluhan negatif**, memberikan gambaran langsung penerimaan publik terhadap resto."
        )

    elif variable_name == "Tingkat Urgensi":
        high_count = int((df["Urgency_Level"] == "Tinggi").sum())
        med_count = int((df["Urgency_Level"] == "Sedang").sum())
        low_count = int((df["Urgency_Level"] == "Rendah").sum())

        high_pct = (high_count / total) * 100.0 if total > 0 else 0.0

        return (
            f"Dari seluruh ulasan keluhan yang masuk, terdapat **{high_count:,} ulasan ({high_pct:.1f}%)** dengan "
            f"status urgensi **Tinggi** yang memerlukan perhatian dan penanganan operasional khusus. "
            f"Penanganan cepat pada kelompok keluhan ini sangat krusial guna mencegah kekecewaan pelanggan yang berulang, "
            f"didukung **{med_count:,} ulasan** berurgensi sedang dan **{low_count:,} ulasan** berurgensi rendah."
        )

    else:  # Ulasan Bergambar
        img_count = int((df["Has_Image"] == "Ya").sum())
        img_pct = (img_count / total) * 100.0 if total > 0 else 0.0

        return (
            f"Sebanyak **{img_count:,} ulasan ({img_pct:.1f}%)** tercatat menyertakan lampiran foto atau gambar "
            f"dalam ulasannya. Adanya bukti visual ini mempermudah manajemen mengidentifikasi kondisi riil penyajian menu "
            f"maupun suasana tempat yang dialami langsung oleh pelanggan di restoran."
        )

def generate_bar_summary(df, variable_name):
    """
    Menghasilkan narasi analisis otomatis untuk Bar Chart sesuai variabel yang dipilih.
    """
    if df is None or df.empty:
        return "Data ulasan tidak tersedia untuk analisis."

    if variable_name == "Isu Aspek Operasional":
        exp_df = expand_categories(df)
        cat_counts = exp_df["Kategori_Tunggal"].value_counts()
        cat_counts = cat_counts[~cat_counts.index.str.lower().isin(["", "nan", "none"])]

        if not cat_counts.empty:
            top_cat = cat_counts.index[0]
            top_val = int(cat_counts.iloc[0])
            least_cat = cat_counts.index[-1]
            least_val = int(cat_counts.iloc[-1])

            return (
                f"Fokus aspek operasional yang paling sering disampaikan konsumen berada pada kategori **{top_cat}** "
                f"dengan total **{top_val:,} ulasan**. Aspek ini menjadi area yang paling banyak menarik perhatian "
                f"pelanggan, sementara aspek **{least_cat}** mencatat interaksi terendah (**{least_val:,} ulasan**) "
                f"dan relatif paling stabil dari sorotan keluhan."
            )
        else:
            return "Kategori operasional belum terpetakan dalam dataset ini."

    else:  # Sebaran Rating Bintang
        rating_series = pd.to_numeric(df["Rating"], errors="coerce").dropna()
        if not rating_series.empty:
            avg_rating = float(rating_series.mean())
            mode_rating = int(rating_series.mode()[0])
            mode_count = int((rating_series == mode_rating).sum())

            star_4_5 = int((rating_series >= 4).sum())
            star_4_5_pct = (star_4_5 / len(rating_series)) * 100.0

            return (
                f"Tingkat kepuasan konsumen secara keseluruhan menunjukkan skor rata-rata **{avg_rating:.2f} dari 5.0**, "
                f"dengan ulasan nilai **bintang {mode_rating}** menjadi penilaian yang paling sering diberikan oleh "
                f"konsumen sebanyak **{mode_count:,} ulasan**. Total pelanggan yang puas (rating bintang 4-5) "
                f"mencapai **{star_4_5_pct:.1f}%** ({star_4_5:,} ulasan)."
            )
        else:
            return "Data rating belum tersedia dalam dataset ini."

def format_summary_html(text: str) -> str:
    """
    Mengonversi sintaks markdown **teks** menjadi tag <strong>teks</strong> murni
    agar tercetak tebal sempurna di dalam komponen HTML.
    """
    if not text:
        return ""
    return re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #f8fafc; font-weight: 700;">\1</strong>', text)

def render_dashboard_view():
    """
    Menampilkan antarmuka Halaman Executive Dashboard:
    1. Header & Deskripsi Halaman
    2. KPI Metrics Row (4 kartu ringkasan di atas)
    3. Interactive Donut Chart (kiri) & Interactive Bar Chart (kanan)
    4. Summary Box di bawah masing-masing grafik
    """
    render_page_header(
        "📊 Executive Dashboard",
        "Ringkasan performa menyeluruh, sentimen pelanggan, dan aspek operasional restoran."
    )

    # Validasi keberadaan dataset aktif
    if "df" not in st.session_state or st.session_state.df is None or st.session_state.df.empty:
        with st.container(border=True):
            st.warning("⚠️ Dataset ulasan belum dimuat.")
            st.write("Silakan muat dataset ulasan melalui menu **Upload & Template** terlebih dahulu untuk melihat visualisasi metrik.")
            if st.button("Buka Halaman Upload & Template", key="btn_go_upload"):
                st.session_state.current_page = "📁 Upload & Template"
                st.rerun()
        return

    df = st.session_state.df

    # 1. KPI Metrics Row (4 Kartu Ringkasan)
    kpi_data = calculate_kpi_metrics(df)
    render_kpi_row(kpi_data)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Dua Kolom Grafik Interaktif
    col_left, col_right = st.columns(2)

    # Kolom Kiri: Donut Chart
    with col_left:
        with st.container(border=True):
            st.markdown("### Proporsi Metrik Ulasan")
            donut_selection = st.selectbox(
                "Pilih Variabel Donut Chart:",
                ["Distribusi Sentimen", "Tingkat Urgensi", "Ulasan Bergambar"],
                key="select_donut_var"
            )

            donut_fig = create_donut_chart(df, donut_selection)
            st.plotly_chart(donut_fig, width="stretch", config={"displayModeBar": False})

            # Summary Box Donut
            donut_text = generate_donut_summary(df, donut_selection)
            donut_html = format_summary_html(donut_text)
            st.html(f"""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 16px 20px;
                margin-top: 12px;
                min-height: 115px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-weight: 700; font-size: 0.95rem; color: #f8fafc; margin-bottom: 8px;">Analisis {donut_selection}:</div>
                <p style="font-size: 0.92rem; color: #cbd5e1; line-height: 1.6; margin: 0;">{donut_html}</p>
            </div>
            """)

    # Kolom Kanan: Bar Chart
    with col_right:
        with st.container(border=True):
            st.markdown("### Distribusi Frekuensi Ulasan")
            bar_selection = st.selectbox(
                "Pilih Variabel Bar Chart:",
                ["Isu Aspek Operasional", "Sebaran Rating Bintang"],
                key="select_bar_var"
            )

            bar_fig = create_bar_chart(df, bar_selection)
            st.plotly_chart(bar_fig, width="stretch", config={"displayModeBar": False})

            # Summary Box Bar
            bar_text = generate_bar_summary(df, bar_selection)
            bar_html = format_summary_html(bar_text)
            st.html(f"""
            <div style="
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 16px 20px;
                margin-top: 12px;
                min-height: 115px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-weight: 700; font-size: 0.95rem; color: #f8fafc; margin-bottom: 8px;">Analisis {bar_selection}:</div>
                <p style="font-size: 0.92rem; color: #cbd5e1; line-height: 1.6; margin: 0;">{bar_html}</p>
            </div>
            """)

    # Menonaktifkan fitur ketik/pencarian manual pada dropdown agar murni menjadi menu klik
    st.html("""
    <script>
    function disableSelectboxTyping() {
        const inputs = document.querySelectorAll('div[data-testid="stSelectbox"] input');
        inputs.forEach(input => {
            input.setAttribute('readonly', 'readonly');
            input.style.caretColor = 'transparent';
            input.style.cursor = 'pointer';
            if (!input.dataset.noTypeBound) {
                input.dataset.noTypeBound = 'true';
                input.addEventListener('keydown', (e) => {
                    if (!['ArrowDown', 'ArrowUp', 'Enter', 'Escape', 'Tab'].includes(e.key)) {
                        e.preventDefault();
                    }
                });
            }
        });
    }
    disableSelectboxTyping();
    const observer = new MutationObserver(disableSelectboxTyping);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_javascript=True)
