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
        --nls-muted: #66727d;
        --nls-rule: #d9dee3;
        --nls-accent: #247b78;
    }
    [data-testid="stAppViewContainer"] {
        background: #f4f5f6;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--nls-rule);
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    .site-kicker {
        color: var(--nls-accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .site-title {
        color: var(--nls-ink);
        font-size: clamp(2rem, 4vw, 3.35rem);
        font-weight: 650;
        letter-spacing: -0.035em;
        line-height: 1.05;
        margin: 0;
    }
    .site-intro {
        color: var(--nls-muted);
        font-size: 1.02rem;
        line-height: 1.65;
        margin: 0.8rem 0 1.5rem;
        max-width: 780px;
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


def page_header(kicker: str, title: str, introduction: str) -> None:
    st.markdown(
        f"""
        <div class="site-kicker">{kicker}</div>
        <h1 class="site-title">{title}</h1>
        <p class="site-intro">{introduction}</p>
        """,
        unsafe_allow_html=True,
    )


def data_downloads(folder: str, heading: str) -> None:
    files = sorted((DATA_DIR / folder).glob("*.csv"))
    with st.expander(heading, expanded=False):
        st.caption(
            "These compact files contain the aggregated values used by the "
            "visualisations. The full master catalogue is not loaded by this website."
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
        "About the method",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.caption(
    "Publication geography is inferred primarily from the Publisher field. "
    "It does not describe the subject geography of every catalogue record."
)

if page == "Catalogue overview":
    page_header(
        "Page 1",
        "Catalogue Metadata Overview",
        "See which catalogue fields are present, how publication-place metadata "
        "is interpreted, and where reliably identified publication places are located.",
    )
    components.html(
        load_html("page1_overview.html"),
        height=1900,
        scrolling=False,
    )
    data_downloads("page1", "Download Page 1 data")

elif page == "Publisher relationships":
    page_header(
        "Page 2",
        "Publisher Relationships",
        "Compare publication-place outcomes by material type, decade and language. "
        "Use each chart's buttons to switch between the full catalogue and records "
        "with an identified Scottish publication place.",
    )
    components.html(
        load_html("page2_relationships.html"),
        height=2380,
        scrolling=False,
    )
    data_downloads("page2", "Download Page 2 data")

else:
    page_header(
        "Method",
        "What these visualisations represent",
        "The website presents aggregate outputs from a validated catalogue master "
        "dataset. It does not clean or classify records while a visitor is browsing.",
    )

    st.markdown(
        """
        ### Publication-place interpretation

        Publication geography is derived primarily from the original **Publisher**
        field. Every record remains in one mutually exclusive metadata outcome:

        - **Place extracted** — a supported rule identified a publication place.
        - **Publisher missing** — the original Publisher field is empty.
        - **Place unresolved** — Publisher text exists but no supported place matched.
        - **Explicitly unknown / ambiguous** — the source is uncertain or cannot be
          classified reliably.

        ### Scotland focus

        “Scotland focus” includes only records where:

        ```text
        publication_metadata_status == "Place extracted"
        geography == "Scotland"
        ```

        It does **not** mean all Scottish material. Missing or unresolved Publisher
        records cannot be assigned to Scotland and are therefore excluded from the
        Scotland numerator and denominator.

        ### Data architecture

        The notebooks process the full catalogue once and export small aggregate CSV
        and Plotly HTML files. This Streamlit site displays those outputs; it does not
        load the multi-million-row master Parquet file.
        """
    )
