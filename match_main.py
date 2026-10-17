"""Main match statistics view."""
import streamlit as st

def render_main(frame):
    st.dataframe(frame, use_container_width=True, hide_index=True)
