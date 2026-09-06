import os
import sys
import streamlit as st

# Konfigurasi path root agar modul internal dapat diimpor dengan aman
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

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

def main():
    # Sidebar Navigasi
    st.sidebar.title("🍽️ Resto Analytics")
    st.sidebar.markdown("Sistem Analisis Sentimen & Wawasan Operasional Restoran")
    st.sidebar.markdown("---")
    
    # Pemetaan Menu Halaman
    menu_options = {
        "📤 Upload & Template": render_upload_view,
        "📊 Executive Dashboard": render_dashboard_view,
        "💬 Tanya AI & Carousel": render_tanya_ai_view,
        "🏷️ 5 Kata Tren": render_kata_tren_view,
        "🔍 Dropdown Kategori": render_dropdown_view,
        "⚙️ Pengaturan": render_settings_view
    }
    
    # Widget Navigasi Radio
    selected_page = st.sidebar.radio(
        "Pilih Halaman:",
        options=list(menu_options.keys()),
        index=1  # Default ke Executive Dashboard
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Automated Web Scraper & AI Sentiment Classifier v1.0")
    
    # Routing ke View Terpilih
    view_function = menu_options.get(selected_page)
    if view_function:
        view_function()

if __name__ == "__main__":
    main()
