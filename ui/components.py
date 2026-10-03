import html

import streamlit as st


def metric_card(label: str, value: str, help_text: str, css_class: str = "") -> None:
    st.html(
        f"""
        <div class="card {css_class}">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-help">{html.escape(help_text)}</div>
        </div>
        """
    )


def section_title(text: str) -> None:
    st.html(f'<div class="section-title">{html.escape(text)}</div>')
