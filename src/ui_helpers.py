"""Shared page chrome so every RelaxiTaxi page looks and feels consistent."""
import streamlit as st

_SHARED_CSS = """
<style>
    [data-testid="stSidebar"] { display: none; }

    div[data-testid="stForm"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.02);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
    }

    .stButton > button, .stFormSubmitButton > button {
        transition: transform 0.1s ease, filter 0.1s ease;
    }

    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        filter: brightness(1.08);
    }
</style>
"""


def setup_page(title: str, icon: str = "🚕") -> None:
    """Set the page config and shared styling. Call first, before any other st.* command."""
    st.set_page_config(page_title=title, page_icon=icon, layout="centered")
    st.markdown(_SHARED_CSS, unsafe_allow_html=True)


def hide_sidebar() -> None:
    """Apply just the shared CSS, for pages that must not call set_page_config again."""
    st.markdown(_SHARED_CSS, unsafe_allow_html=True)
