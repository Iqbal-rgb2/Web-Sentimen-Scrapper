import streamlit as st
from dashboard.components.header import render_page_header

def render_settings_view():
    """
    Menampilkan antarmuka Halaman Pengaturan.
    """
    render_page_header(
        "⚙️ Pengaturan",
        "Konfigurasi API key Gemini dan preferensi sistem."
    )
    st.info("Fitur konfigurasi API Key dan preferensi sistem akan diimplementasikan pada Langkah 4.6.")
