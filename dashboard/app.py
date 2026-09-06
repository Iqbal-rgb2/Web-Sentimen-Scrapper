import os
import sys
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

# Konfigurasi path root agar modul internal dapat diimpor dengan aman
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.backend_engine import load_clean_data
from dashboard.views.upload_view import render_upload_view
from dashboard.views.dashboard_view import render_dashboard_view
from dashboard.views.tanya_ai_view import render_tanya_ai_view
from dashboard.views.kata_tren_view import render_kata_tren_view
from dashboard.views.dropdown_view import render_dropdown_view
from dashboard.views.settings_view import render_settings_view

# Konfigurasi Halaman Utama Streamlit
st.set_page_config(
    page_title="Dashboard Analisis Sentimen Restoran",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(show_spinner="Memuat dataset ulasan awal...")
def get_initial_data():
    """
    Memuat dataset default lokal menggunakan backend engine dengan caching Streamlit.
    """
    default_data_path = os.path.join(ROOT_DIR, "data", "processed", "raw_reviews2_enriched2.csv")
    if os.path.exists(default_data_path):
        return load_clean_data(default_data_path)
    return pd.DataFrame()

def init_session_state():
    """
    Inisialisasi variabel global pada st.session_state (Langkah 3.2):
    1. st.session_state.df: DataFrame aktif (default: memuat data lokal awal).
    2. st.session_state.gemini_key: API Key Gemini dari .env atau input pengguna.
    3. st.session_state.active_insight_index: Indeks wawasan aktif (0-9) Carousel 10 Insight.
    4. st.session_state.selected_tag: Kata kunci, kategori, dan sentimen terpilih dari 5 Kata Tren.
    """
    # 1. Inisialisasi API Key Gemini
    if "gemini_key" not in st.session_state:
        load_dotenv(os.path.join(ROOT_DIR, ".env"))
        st.session_state.gemini_key = os.getenv("GEMINI_API_KEY", "")

    # 2. Inisialisasi DataFrame Aktif
    if "df" not in st.session_state:
        try:
            initial_df = get_initial_data()
            st.session_state.df = initial_df.copy() if not initial_df.empty else initial_df
        except Exception as e:
            st.session_state.df = pd.DataFrame()
            st.error(f"Gagal memuat dataset ulasan awal: {e}")

    # 3. Inisialisasi Indeks Wawasan Aktif untuk Carousel 10 Insight
    if "active_insight_index" not in st.session_state:
        st.session_state.active_insight_index = 0

    # 4. Inisialisasi Filter Tag Terpilih dari Halaman 5 Kata Tren
    if "selected_tag" not in st.session_state:
        st.session_state.selected_tag = {
            "keyword": None,
            "category": None,
            "sentiment": None
        }

def inject_custom_css():
    """
    Injeksi styling kustom (Adaptive Slate & Modern Indigo).
    Tulisan nyaman dibaca (ukuran proporsional), menghilangkan bulatan radio,
    dan warna kartu yang bersih alami di tempat gelap maupun terang.
    """
    st.markdown("""
    <style>
    /* 1. Sembunyikan bulatan radio bawaan browser secara tuntas */
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] label svg,
    div[data-testid="stRadio"] input[type="radio"],
    [data-baseweb="radio"] > div:first-child {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
    }

    /* 2. Format setiap opsi menu menjadi kartu tombol modern */
    div[data-testid="stRadio"] label,
    [data-baseweb="radio"] {
        background-color: transparent !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        width: 100% !important;
        border: 1px solid transparent !important;
        transition: all 0.15s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Ukuran tulisan menu dibuat lebih besar dan jelas dibaca */
    div[data-testid="stRadio"] label p,
    [data-baseweb="radio"] p {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        line-height: 1.4 !important;
        color: var(--text-color) !important;
    }

    /* Efek hover pada menu */
    div[data-testid="stRadio"] label:hover,
    [data-baseweb="radio"]:hover {
        background-color: rgba(128, 128, 128, 0.08) !important;
        border-color: rgba(128, 128, 128, 0.15) !important;
    }

    /* Menu yang sedang aktif / terpilih */
    div[data-testid="stRadio"] label:has(input:checked),
    [data-baseweb="radio"]:has(input:checked) {
        background-color: rgba(99, 102, 241, 0.14) !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
        border-left: 4px solid #6366f1 !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) p,
    [data-baseweb="radio"]:has(input:checked) p {
        font-weight: 700 !important;
    }

    /* 3. Panel Expander Sidebar */
    div[data-testid="stSidebar"] div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        background: var(--secondary-background-color) !important;
    }

    /* 4. Tombol Aksi */
    div[data-testid="stSidebar"] button {
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    div[data-testid="stSidebar"] button:hover {
        border-color: #6366f1 !important;
        color: #6366f1 !important;
    }

    /* 5. Garis Pembatas Halus */
    hr {
        border: none !important;
        height: 1px !important;
        background: rgba(128, 128, 128, 0.2) !important;
        margin: 12px 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 1. Inisialisasi Session State di awal aplikasi
    init_session_state()

    # 2. Injeksi Styling Kustom
    inject_custom_css()

    # 3. Sidebar Header Card Ringkas & Bersih
    st.sidebar.markdown("""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 14px;
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        margin-bottom: 16px;
    ">
        <span style="font-size: 1.15rem; font-weight: 700;">🍽️ Resto Analytics</span>
        <span style="
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 8px;
            background: rgba(99, 102, 241, 0.15);
            color: #6366f1;
            border-radius: 6px;
        ">v1.0</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Pemetaan Menu Halaman
    menu_options = {
        "📤 Upload & Template": render_upload_view,
        "📊 Executive Dashboard": render_dashboard_view,
        "💬 Tanya AI & Carousel": render_tanya_ai_view,
        "🏷️ 5 Kata Tren": render_kata_tren_view,
        "🔍 Filter Kategori": render_dropdown_view,
        "⚙️ Pengaturan": render_settings_view
    }
    
    # Widget Navigasi Radio
    selected_page = st.sidebar.radio(
        "Pilih Menu",
        options=list(menu_options.keys()),
        index=1,
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")

    # Panel Informasi Status Session State (Format Grid Ringkas)
    with st.sidebar.expander("⚡ Status Sistem", expanded=False):
        df_count = len(st.session_state.df) if "df" in st.session_state and not st.session_state.df.empty else 0
        has_key = bool(st.session_state.get("gemini_key"))
        key_label = "Tersedia" if has_key else "Belum Diatur"
        key_color = "#10b981" if has_key else "#f59e0b"
        
        carousel_idx = st.session_state.get("active_insight_index", 0)
        selected_tag = st.session_state.get("selected_tag", {})
        kw = selected_tag.get("keyword") if selected_tag else None
        tag_label = kw if kw else "Semua"

        st.markdown(f"""
        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 12px;
        ">
            <div style="
                background: rgba(128, 128, 128, 0.1);
                border-radius: 8px;
                padding: 8px 10px;
            ">
                <div style="font-size: 0.72rem; opacity: 0.7; font-weight: 600;">Data</div>
                <div style="font-size: 0.95rem; font-weight: 700; margin-top: 2px;">{df_count:,} baris</div>
            </div>
            <div style="
                background: rgba(128, 128, 128, 0.1);
                border-radius: 8px;
                padding: 8px 10px;
            ">
                <div style="font-size: 0.72rem; opacity: 0.7; font-weight: 600;">Gemini AI</div>
                <div style="font-size: 0.92rem; font-weight: 700; margin-top: 2px; color: {key_color};">{key_label}</div>
            </div>
            <div style="
                background: rgba(128, 128, 128, 0.1);
                border-radius: 8px;
                padding: 8px 10px;
            ">
                <div style="font-size: 0.72rem; opacity: 0.7; font-weight: 600;">Carousel</div>
                <div style="font-size: 0.95rem; font-weight: 700; margin-top: 2px;">Slide #{carousel_idx}</div>
            </div>
            <div style="
                background: rgba(128, 128, 128, 0.1);
                border-radius: 8px;
                padding: 8px 10px;
            ">
                <div style="font-size: 0.72rem; opacity: 0.7; font-weight: 600;">Tag Filter</div>
                <div style="font-size: 0.92rem; font-weight: 700; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{tag_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("Index +1", key="btn_test_idx", use_container_width=True):
                st.session_state.active_insight_index = (st.session_state.active_insight_index + 1) % 10
                st.rerun()
        with col_t2:
            if st.button("Set Tag", key="btn_test_set_tag", use_container_width=True):
                st.session_state.selected_tag = {
                    "keyword": "pelayanan",
                    "category": "Layanan & Staf",
                    "sentiment": "Positif"
                }
                st.rerun()
        if st.button("Reset Filter", key="btn_test_rst_tag", use_container_width=True):
            st.session_state.selected_tag = {
                "keyword": None,
                "category": None,
                "sentiment": None
            }
            st.rerun()
    
    # Routing ke View Terpilih
    view_function = menu_options.get(selected_page)
    if view_function:
        view_function()

if __name__ == "__main__":
    main()
