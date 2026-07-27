from pathlib import Path

import streamlit as st

from page1_overview import render_page1
from page2_dashboard import render_page2
from page3_missingness import render_page3


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"

st.set_page_config(
    page_title="NLS Catalogue Visualisation",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#24272b; --muted:#687078; --rule:#d9dee3; }
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stMarkdownContainer"],
    button, input, select, textarea {
        font-family:Arial, Helvetica, sans-serif !important;
        font-weight:400;
    }
    [data-testid="stAppViewContainer"] { background:#f4f5f6; color:var(--ink); }
    [data-testid="stSidebar"] {
        background:#fff; border-right:1px solid var(--rule);
    }
    [data-testid="stSidebar"] *,
    [data-testid="stExpander"] *,
    [data-testid="stMarkdownContainer"] { color:var(--ink); }
    .block-container {
        max-width:1280px; padding-top:1.4rem; padding-bottom:3rem;
    }
    h1,h2,h3,p,[data-testid="stCaptionContainer"] {
        font-family:Arial, Helvetica, sans-serif !important;
        white-space:normal !important;
        overflow-wrap:break-word !important;
        word-break:normal !important;
        overflow:visible !important;
        text-overflow:clip !important;
    }
    h1 { font-weight:600 !important; letter-spacing:-.025em; }
    h2,h3 { font-weight:400 !important; letter-spacing:0; }
    p, label, [data-testid="stCaptionContainer"] {
        font-weight:400 !important;
    }
    strong, b { font-weight:600 !important; }
    .page-intro {
        color:var(--muted); font-size:1.04rem; line-height:1.65;
        max-width:980px; margin-bottom:.5rem;
    }
    .section-label {
        color:#52606b; font-size:.78rem; font-weight:400;
        letter-spacing:.1em; margin:2.5rem 0 .45rem;
        text-transform:uppercase;
    }
    .page-section-rule {
        border-top:3px solid var(--ink);
        margin-top:1.35rem;
        height:.35rem;
    }
    div[data-testid="stSegmentedControl"] { margin:.35rem 0 .8rem; }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background:#247B78 !important; border-color:#247B78 !important;
        color:#fff !important; font-weight:400 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="false"] {
        background:#fff !important; border:1px solid #aeb7bf !important;
        color:var(--ink) !important;
    }
    div[data-testid="stAlert"] { border-left:4px solid #247B78; }
    div[data-testid="stDownloadButton"] button {
        border-color:var(--rule); width:100%;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        font-family:Arial, Helvetica, sans-serif !important;
        font-weight:400 !important;
    }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def data_downloads(folder: str, heading: str) -> None:
    files = sorted((DATA_DIR / folder).glob("*.csv"))
    with st.expander(heading, expanded=False):
        st.caption(
            "These small files contain the values used in the charts. "
            "The full catalogue dataset is not loaded by this website."
        )
        for path in files:
            st.download_button(
                label=f"Download {path.name}",
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/csv",
                key=f"{folder}-{path.name}",
            )


st.sidebar.markdown("## NLS Catalogue")
st.sidebar.caption("Publication-place metadata visualisation")
page = st.sidebar.radio(
    "Explore",
    options=[
        "Catalogue overview",
        "Publication-place patterns",
        "Missingness and uncertainty",
    ],
    label_visibility="collapsed",
)

if page == "Catalogue overview":
    render_page1(DATA_DIR / "page1", data_downloads)
elif page == "Publication-place patterns":
    render_page2(DATA_DIR / "page2", data_downloads)
else:
    render_page3(DATA_DIR / "page3", data_downloads)
