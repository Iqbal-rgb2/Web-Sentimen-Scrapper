import streamlit as st
from dashboard.components.header import render_page_header

def render_dropdown_view():
    """
    Menampilkan antarmuka Halaman Filter Kategori.
    """
    render_page_header(
        "🔍 Filter Kategori",
        "Penyaringan data ulasan mendalam berdasarkan kategori operasional dan sentimen."
    )
    st.info("Fitur filter multi-kriteria dan editor koreksi ulasan akan diimplementasikan pada Langkah 4.5.")
