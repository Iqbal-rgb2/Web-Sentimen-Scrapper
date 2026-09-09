import streamlit as st

def render_page_header(title: str, caption: str):
    """
    Merender header terstandar untuk setiap halaman:
    - Judul dengan emoji dan tipografi tebal
    - Subtitle/caption deskriptif
    - Terintegrasi dengan CSS Sticky Header agar tetap berada di posisi atas saat halaman di-scroll
    """
    st.html(
        f'<div class="page-sticky-header"><h1 class="page-sticky-title">{title}</h1><p class="page-sticky-caption">{caption}</p></div>'
    )
