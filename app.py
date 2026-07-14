import streamlit as st

from auth import login_inicio
from config import APP_LAYOUT, APP_TITLE
from reports import render_dashboard
from ui_components import _inject_loading_overlay

try:
    from ui_components import inject_gerencial_theme
except ImportError:
    def inject_gerencial_theme():
        return None


def main():
    st.set_page_config(page_title=APP_TITLE, layout=APP_LAYOUT, initial_sidebar_state="expanded")
    app_code_version = "lazy_views_perf_v1"
    if st.session_state.get("_APP_CODE_VERSION") != app_code_version:
        st.cache_data.clear()
        for key in [
            "dfg_det_cache",
            "npn_fija_cache",
            "npn_movil_cache",
            "_dvz_mtime",
            "_npn_schema_version",
            "_COMMON_TABLES_PRELOADED",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["_APP_CODE_VERSION"] = app_code_version
    inject_gerencial_theme()
    login_inicio()
    _inject_loading_overlay()
    render_dashboard()


if __name__ == "__main__":
    main()
