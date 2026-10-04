import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

MIME_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@lru_cache(maxsize=4)
def file_to_data_uri(path: Path) -> str:
    """Convert a local image/SVG to a browser-readable data URI."""
    if not path.exists():
        return ""
    mime = MIME_TYPES.get(path.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def inject_readability_styles() -> None:
    """Dark, high-contrast text on the light content panels (sidebar and hero keep their own)."""
    st.html(
        """
        <style>
        [data-testid="stMain"] {
            color: #0B2239;
            font-size: 15px;
            line-height: 1.45;
        }

        [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
        [data-testid="stMain"] [data-testid="stWidgetLabel"] p,
        [data-testid="stMain"] [data-testid="stWidgetLabel"] label {
            color: #0B2239;
        }

        [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
            font-weight: 600;
        }

        [data-testid="stMain"] .stButton > button {
            height: auto;
            min-height: 2.6rem;
            padding: .45rem .65rem;
            white-space: normal;
        }

        [data-testid="stMain"] .stButton > button p {
            margin: 0;
            line-height: 1.2;
            white-space: normal;
            overflow-wrap: anywhere;
            text-overflow: clip;
        }

        /* Captions are theme-grey by default; darken so they read over the picture */
        [data-testid="stMain"] [data-testid="stCaptionContainer"],
        [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
            color: #1B3550 !important;
            opacity: 1 !important;
        }

        [data-testid="stHeading"] h1,
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3 {
            color: #06243f;
            text-shadow: none;
        }

        [data-testid="stHeading"] h1 {
            font-size: 30px;
            line-height: 1.2;
        }

        [data-testid="stHeading"] h2 {
            font-size: 23px;
            line-height: 1.25;
        }

        [data-testid="stHeading"] h3 {
            font-size: 19px;
            line-height: 1.3;
        }

        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricLabel"] {
            color: #35506B !important;
        }

        [data-testid="stMetricValue"] {
            color: #06243f !important;
        }

        /* Alerts: solid light surface + dark text instead of translucent tints */
        [data-testid="stAlert"] {
            background-color: rgba(255,255,255,.93) !important;
            border: 1px solid rgba(8,42,74,.18);
            border-left: 5px solid #1479D1;
            border-radius: 12px;
        }

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] li,
        [data-testid="stAlert"] div {
            color: #0B2239 !important;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            background: rgba(255,255,255,.94);
            border-radius: 12px;
        }

        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary p {
            color: #0B2239 !important;
            font-weight: 600;
        }

        [data-testid="stExpander"] {
            border-radius: 12px;
            overflow: hidden;
        }

        /* Fixed bottom bar (chat input) should not be an opaque white strip */
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div {
            background: transparent !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: #46607A !important;
            opacity: 1;
        }

        [data-testid="stChatMessage"] {
            background-color: rgba(255,255,255,.90);
            border: 1px solid rgba(8,42,74,.12);
            border-radius: 14px;
        }

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li {
            color: #0B2239;
        }

        [data-testid="stFileUploaderDropzone"] {
            background-color: rgba(255,255,255,.92);
            border: 1px dashed rgba(8,42,74,.35);
        }

        [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploaderDropzone"] p {
            color: #0B2239 !important;
        }

        [data-testid="stTickBarMin"],
        [data-testid="stTickBarMax"],
        [data-testid="stSliderThumbValue"] {
            color: #0B2239 !important;
        }

        [data-testid="stSpinner"] p {
            color: #0B2239;
        }

        /* Section titles rendered as custom HTML */
        .section-title {
            color: #06243f;
            font-size: 18px;
            line-height: 1.3;
            text-shadow: none;
        }
        </style>
        """
    )


def inject_app_background(path: Path | None) -> None:
    """Place the background picture only in the sidebar; keep the app canvas clean."""
    if path is None:
        return
    uri = file_to_data_uri(path)
    st.html(
        f"""
        <style>
        .stApp {{
            background: #F1F5F7 !important;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {{
            background: #F1F5F7 !important;
        }}

        .block-container {{
            max-width: 1500px;
            background: transparent;
            border: 0;
            border-radius: 0;
            box-shadow: none;
            margin: 0 auto;
            padding: 1.35rem 2rem 2.25rem;
        }}

        [data-testid="stSidebar"] {{
            background-image:
                linear-gradient(rgba(5,34,57,.84), rgba(5,34,57,.76)),
                url("{uri}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: transparent;
        }}

        .card,
        .callout,
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #FFFFFF;
        }}

        .recommendation {{
            background: #FFF8E6;
        }}
        </style>
        """
    )


def inject_styles(bg_path: Path) -> None:
    bg_uri = file_to_data_uri(bg_path)
    st.html(
        f"""
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {{
        --navy: #082A4A;
        --navy2: #0D3B66;
        --blue: #1479D1;
        --cyan: #36B8E8;
        --green: #20A66A;
        --mint: #EAF8F1;
        --bg: #F4F8FB;
        --text: #102A43;
        --muted: #46607A;
        --border: #DCE7EF;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: var(--bg);
    }}

    /* SIDEBAR */

    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            #062847 0%,
            #0B3C63 65%,
            #082A4A 100%
        );

        border-right: 1px solid rgba(255,255,255,.08);
    }}

    [data-testid="stSidebar"] * {{
        color: #F7FBFF !important;
    }}

    .brand {{
        padding: 8px 6px 22px;
        border-bottom: 1px solid rgba(255,255,255,.13);
        margin-bottom: 18px;
    }}

    .brand-title {{
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -.8px;
    }}

    .brand-title span {{
        color: #41D89A;
    }}

    .brand-sub {{
        font-size: 11px;
        color: #C9DFED !important;
        margin-top: 2px;
    }}

    /* HERO */

    .hero {{
        min-height: 210px;

        border-radius: 14px;

        overflow: hidden;

        position: relative;

        background-image:
            linear-gradient(
                90deg,
                rgba(5,36,66,.94) 0%,
                rgba(7,54,83,.78) 46%,
                rgba(7,54,83,.18) 100%
            ),
            url("{bg_uri}");

        background-size: cover;

        background-position: center;

        padding: 32px 36px;

        margin-bottom: 18px;

        box-shadow:
            0 14px 35px rgba(8,42,74,.14);
    }}

    .hero h1 {{
        color: white;

        font-size: 36px;

        line-height: 1.05;

        margin: 0 0 10px;

        font-weight: 800;

        letter-spacing: 0;
    }}

    .hero h1 span {{
        color: #43D79A;
    }}

    .hero p {{
        color: #E4F2FA;

        font-size: 15px;

        max-width: 650px;

        margin: 0;

        line-height: 1.55;
    }}

    /* CARDS */

    .section-title {{
        font-size: 18px;

        color: var(--text);

        font-weight: 800;

        margin: 18px 0 10px;
    }}

    .card {{
        background: white;

        border: 1px solid var(--border);

        border-radius: 12px;

        padding: 16px;

        box-shadow:
            0 7px 22px rgba(13,59,102,.06);
    }}

    .metric-label {{
        color: var(--muted);

        font-size: 13px;

        font-weight: 600;
    }}

    .metric-value {{
        color: var(--text);

        font-size: 26px;

        font-weight: 800;

        margin: 6px 0;
    }}

    .metric-help {{
        color: var(--muted);

        font-size: 11px;
    }}

    .pill {{
        display: inline-block;

        padding: 5px 10px;

        border-radius: 999px;

        font-size: 11px;

        font-weight: 700;
    }}

    .pill-green {{
        background: #E5F7EF;

        color: #118357;
    }}

    .pill-blue {{
        background: #E7F2FC;

        color: #1268AE;
    }}

    .pill-yellow {{
        background: #FFF5D9;

        color: #9A6A00;
    }}

    .callout {{
        background:
            linear-gradient(
                135deg,
                #F0FAF6,
                #EAF6FF
            );

        border: 1px solid #CDE9DD;

        border-radius: 16px;

        padding: 18px;
    }}

    .small-muted {{
        color: var(--muted);

        font-size: 12px;
    }}

    .big-number {{
        font-size: 38px;

        font-weight: 800;

        color: var(--navy);
    }}

    .recommendation {{
        background: #FFF8E6;

        border: 1px solid #F4D889;

        border-radius: 16px;

        padding: 20px;
    }}

    /* STREAMLIT METRICS */

    div[data-testid="stMetric"] {{
        background: white;

        border: 1px solid var(--border);

        border-radius: 14px;

        padding: 12px;
    }}

    /* BUTTONS */

    .stButton > button {{
        border-radius: 10px;

        font-weight: 700;

        border: 1px solid #CFE0EC;
    }}

    .stButton > button[kind="primary"] {{
        background:
            linear-gradient(
                90deg,
                #1479D1,
                #159A91
            );

        color: white;

        border: 0;
    }}

    footer {{
        visibility: hidden;
    }}

    </style>
    """
    )
