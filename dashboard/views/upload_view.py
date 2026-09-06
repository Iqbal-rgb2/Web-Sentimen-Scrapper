import streamlit as st

def render_upload_view():
    """
    Menampilkan antarmuka Halaman Upload & Template.
    """
    st.title("📤 Upload & Template Data Ulasan")
    st.markdown("Unggah berkas CSV ulasan baru atau unduh template standar untuk analisis sentimen.")
    st.info("Fitur detail pemrosesan unggahan berkas akan diimplementasikan pada Langkah 4.1.")
