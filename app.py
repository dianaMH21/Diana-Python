import streamlit as st

from auth import login_inicio
from config import APP_LAYOUT, APP_TITLE
from reports import render_dashboard
from ui_components import _inject_loading_overlay


def main():
    st.set_page_config(page_title=APP_TITLE, layout=APP_LAYOUT, initial_sidebar_state="expanded")
    login_inicio()
    _inject_loading_overlay()
    render_dashboard()


if __name__ == "__main__":
    main()
