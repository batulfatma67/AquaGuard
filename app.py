import streamlit as st

from config import APP_BG_PATH, BG_PATH
from ui.pages import (
    assistant,
    decision,
    document_rag,
    farm_intelligence,
    farm_setup,
    overview,
    reports,
    scenarios,
    water_account,
)
from ui.state import init_state
from ui.styles import inject_app_background, inject_readability_styles, inject_styles

st.set_page_config(
    page_title="AquaGuard AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles(BG_PATH)
inject_app_background(APP_BG_PATH)
inject_readability_styles()
init_state()

PAGES = {
    "🏠  Overview": overview.render,
    "🌱  Farm Profiles": farm_setup.render,
    "🛰️  Farm Intelligence": farm_intelligence.render,
    "💧  Water Account": water_account.render,
    "🛡️  AquaGuard Decision": decision.render,
    "📊  What-If Scenarios": scenarios.render,
    "📄  Reports": reports.render,
    "📚  AI Assistant": document_rag.render,
    "🤖  Calculated Q/A": assistant.render,
}

with st.sidebar:
    st.html(
        """
        <div class="brand">
            <div class="brand-title">💧 Aqua<span>Guard</span></div>
            <div class="brand-sub">SMARTER WATER. HEALTHIER FARMS.</div>
        </div>
        """
    )

    page_label = st.radio(
        "Navigation", list(PAGES), key="nav", label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("AquaGuard AI • Prototype v1.0")
    st.caption("Potential water savings are model estimates, not measured pumping reductions.")

PAGES[page_label]()
