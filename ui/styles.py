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
            text-shadow: 0 1px 6px rgba(255,255,255,.75);
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
            text-shadow: 0 1px 6px rgba(255,255,255,.75);
        }
        </style>
        """
    )


def inject_app_background(path: Path | None) -> None:
    """Background picture kept visible; content sits on frosted-glass panels for readability."""
    if path is None:
        return
    uri = file_to_data_uri(path)
    st.html(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(8,42,74,.00), rgba(8,42,74,.12)),
                url("{uri}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        /* Main content panel: picture shows around and softly through it */
        .block-container {{
            background: rgba(255,255,255,.46);
            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
            border: 1px solid rgba(255,255,255,.55);
            border-radius: 22px;
            box-shadow: 0 18px 50px rgba(8,42,74,.22);
            margin-top: 18px;
            margin-bottom: 18px;
            padding: 2.2rem 2.4rem 3rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg,
                rgba(6,40,71,.80) 0%,
                rgba(11,60,99,.76) 65%,
                rgba(8,42,74,.84) 100%
            );
            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
        }}

        .card,
        .callout,
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: rgba(255,255,255,.90);
        }}

        .recommendation {{
            background: rgba(255,248,230,.92);
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
        min-height: 250px;

        border-radius: 20px;

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

        padding: 42px 46px;

        margin-bottom: 22px;

        box-shadow:
            0 14px 35px rgba(8,42,74,.14);
    }}

    .hero h1 {{
        color: white;

        font-size: 42px;

        line-height: 1.05;

        margin: 0 0 10px;

        font-weight: 800;

        letter-spacing: -1.4px;
    }}

    .hero h1 span {{
        color: #43D79A;
    }}

    .hero p {{
        color: #E4F2FA;

        font-size: 16px;

        max-width: 650px;

        margin: 0;

        line-height: 1.55;
    }}

    /* CARDS */

    .section-title {{
        font-size: 20px;

        color: var(--text);

        font-weight: 800;

        margin: 12px 0 12px;
    }}

    .card {{
        background: white;

        border: 1px solid var(--border);

        border-radius: 16px;

        padding: 19px;

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

        font-size: 29px;

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
