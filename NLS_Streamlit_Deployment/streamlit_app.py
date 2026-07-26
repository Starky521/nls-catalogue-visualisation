from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
VISUAL_DIR = APP_DIR / "visuals"
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
    :root {
        --nls-ink: #1f2933;
        --nls-rule: #d9dee3;
    }
    [data-testid="stAppViewContainer"] {
        background: #f4f5f6;
        color: var(--nls-ink);
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--nls-rule);
    }
    [data-testid="stSidebar"] *,
    [data-testid="stExpander"] *,
    [data-testid="stMarkdownContainer"] {
        color: var(--nls-ink);
    }
    .block-container {
        max-width: 1240px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stDownloadButton"] button {
        border-color: var(--nls-rule);
        width: 100%;
    }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_html(filename: str) -> str:
    return (VISUAL_DIR / filename).read_text(encoding="utf-8")


def data_downloads(folder: str, heading: str) -> None:
    files = sorted((DATA_DIR / folder).glob("*.csv"))
    with st.expander(heading, expanded=False):
        st.caption(
            "These small files contain the numbers used in the charts. "
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
        "Publisher relationships",
    ],
    label_visibility="collapsed",
)

if page == "Catalogue overview":
    components.html(
        load_html("page1_overview.html"),
        height=1980,
        scrolling=False,
    )
    data_downloads("page1", "Download Page 1 data")

else:
    components.html(
        load_html("page2_relationships.html"),
        height=2500,
        scrolling=False,
    )
    data_downloads("page2", "Download Page 2 data")
