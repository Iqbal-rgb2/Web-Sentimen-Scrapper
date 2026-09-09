import streamlit as st
from dashboard.components.header import render_page_header

def render_tanya_ai_view():
    """
    Menampilkan antarmuka Halaman Tanya AI & Carousel.
    """
    render_page_header(
        "💬 Tanya AI & Carousel",
        "Asisten AI dan ringkasan 10 wawasan operasional restoran."
    )
    st.info("Fitur Carousel wawasan dan obrolan AI akan diimplementasikan pada Langkah 4.3.")
