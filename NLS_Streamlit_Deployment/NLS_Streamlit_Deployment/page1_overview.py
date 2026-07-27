from pathlib import Path
from typing import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


INK = "#24272B"
MUTED = "#687078"
GRID = "#EBF0F3"
PRESENT = "#2A7F78"
MISSING = "#C85D61"
UNRESOLVED = "#E39A35"
UNKNOWN = "#6F5AA8"
AMBIGUOUS = "#B58AC7"

PLOT_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "nls-catalogue-overview",
        "scale": 2,
    },
}


@st.cache_data(show_spinner=False)
def load_page1_data(data_dir_text: str) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir_text)
    required = {
        "field_completeness": "page1_field_completeness.csv",
        "publication_status": "page1_publication_status.csv",
        "geography": "page1_geography_distribution.csv",
    }
    data = {}
    for name, filename in required.items():
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Page 1 data file is missing: {filename}")
        data[name] = pd.read_csv(path)
    return data


def base_layout(
    figure: go.Figure,
    title: str,
    subtitle: str,
    height: int,
    left: int,
    bottom: int = 65,
) -> go.Figure:
    figure.update_layout(
        title=dict(
            text=title,
            x=0,
            xanchor="left",
            y=0.96,
            font=dict(size=23, color=INK, family="Arial, Helvetica, sans-serif"),
        ),
        annotations=[
            dict(
                text=subtitle,
                x=0,
                y=1.035,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="left",
                align="left",
                font=dict(size=13, color=MUTED, family="Arial, Helvetica, sans-serif"),
            )
        ],
        height=height,
        margin=dict(l=left, r=45, t=108, b=bottom),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Arial, Helvetica, sans-serif",
            size=14,
            color=INK,
        ),
        hoverlabel=dict(
            font=dict(size=13, color=INK),
            bgcolor="white",
            bordercolor="#D7D9DC",
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.17,
            xanchor="left",
            x=0,
        ),
        bargap=0.20,
    )
    return figure


def percentage_axis(title: str) -> dict:
    return dict(
        title=dict(text=title, standoff=12),
        range=[0, 100],
        ticksuffix="%",
        dtick=20,
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        fixedrange=True,
    )


def completeness_chart(data: pd.DataFrame) -> go.Figure:
    fields = data["field"].astype(str).tolist()
    present = data["present_rate"].astype(float)
    missing = data["missing_rate"].astype(float)
    present_text = [f"{value:.1f}%" for value in present]
    missing_text = [
        f"{value:.1f}%" if value >= 6 else "" for value in missing
    ]

    figure = go.Figure()
    figure.add_bar(
        name="Present",
        y=fields,
        x=present,
        orientation="h",
        marker_color=PRESENT,
        text=present_text,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", family="Arial, Helvetica, sans-serif"),
        customdata=data[["present_count", "total_records"]],
        hovertemplate=(
            "<b>%{y}: information present</b><br>"
            "Records: %{customdata[0]:,}<br>"
            "Percentage: %{x:.1f}%"
            "<extra></extra>"
        ),
    )
    figure.add_bar(
        name="Missing",
        y=fields,
        x=missing,
        orientation="h",
        marker_color=MISSING,
        text=missing_text,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", family="Arial, Helvetica, sans-serif"),
        customdata=data[["missing_count", "total_records"]],
        hovertemplate=(
            "<b>%{y}: information missing</b><br>"
            "Records: %{customdata[0]:,}<br>"
            "Percentage: %{x:.1f}%"
            "<extra></extra>"
        ),
    )
    figure.update_layout(barmode="stack")
    figure.update_xaxes(**percentage_axis("Catalogue records (%)"))
    figure.update_yaxes(
        categoryorder="array",
        categoryarray=fields[::-1],
        fixedrange=True,
    )
    return base_layout(
        figure,
        "Information present in the main catalogue fields",
        "Percentage of records with information present or missing.",
        500,
        left=120,
        bottom=85,
    )


def publication_status_chart(data: pd.DataFrame) -> go.Figure:
    label_map = {"Place extracted": "Place identified"}
    labels = data["status"].replace(label_map).astype(str)
    percentages = data["percentage_of_all_records"].astype(float)
    colours = {
        "Place identified": PRESENT,
        "Publisher missing": MISSING,
        "Place unresolved": UNRESOLVED,
        "Explicitly unknown": UNKNOWN,
        "Ambiguous": AMBIGUOUS,
    }

    figure = go.Figure(
        go.Bar(
            y=labels,
            x=percentages,
            orientation="h",
            marker_color=[colours[label] for label in labels],
            text=[f"{value:.1f}%" for value in percentages],
            textposition="outside",
            cliponaxis=False,
            customdata=data[["count", "denominator"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Records: %{customdata[0]:,}<br>"
                "Percentage of catalogue: %{x:.1f}%"
                "<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(**percentage_axis("Catalogue records (%)"))
    figure.update_yaxes(
        categoryorder="array",
        categoryarray=labels.iloc[::-1].tolist(),
        fixedrange=True,
    )
    return base_layout(
        figure,
        "Publication place information in the catalogue",
        "Every record appears in one result; missing and unclear information remains visible.",
        520,
        left=175,
        bottom=55,
    )


def geography_chart(data: pd.DataFrame) -> go.Figure:
    geography_order = [
        "London",
        "Other UK and Ireland",
        "Overseas",
        "Scotland",
    ]
    values = data.set_index("geography").reindex(geography_order).reset_index()
    colours = {
        "London": "#4C78A8",
        "Other UK and Ireland": "#8F6FB3",
        "Overseas": "#DF8F32",
        "Scotland": "#3E815F",
    }
    percentages = values["percentage_of_identified_records"].astype(float)
    figure = go.Figure(
        go.Bar(
            y=values["geography"],
            x=percentages,
            orientation="h",
            marker_color=[colours[value] for value in values["geography"]],
            text=[f"{value:.1f}%" for value in percentages],
            textposition="outside",
            cliponaxis=False,
            customdata=values[
                ["count", "percentage_of_all_records", "identified_records_total"]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Identified records: %{customdata[0]:,}<br>"
                "Percentage of identified records: %{x:.1f}%<br>"
                "Percentage of full catalogue: %{customdata[1]:.1f}%"
                "<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(**percentage_axis("Records with an identified place (%)"))
    figure.update_yaxes(
        categoryorder="array",
        categoryarray=geography_order[::-1],
        fixedrange=True,
    )
    return base_layout(
        figure,
        "Identified publication places by region",
        "This chart includes only records where a publication place was identified reliably.",
        485,
        left=190,
        bottom=55,
    )


def show_chart(figure: go.Figure) -> None:
    st.markdown('<div class="page-section-rule"></div>', unsafe_allow_html=True)
    st.plotly_chart(
        figure,
        use_container_width=True,
        config=PLOT_CONFIG,
    )


def render_page1(
    data_dir: Path,
    downloads: Callable[[str, str], None] | None = None,
) -> None:
    # EDITABLE PAGE 1 TEXT: change the title and introduction below.
    st.title("Catalogue Information Overview")
    st.markdown(
        """
        <p class="page-intro">
        This page shows which catalogue fields contain information, how many
        publication places can be identified, and where those places are.
        Move the pointer over a chart to see record counts and percentages.
        </p>
        """,
        unsafe_allow_html=True,
    )

    try:
        data = load_page1_data(str(data_dir))
    except Exception as error:
        st.error(f"Page 1 could not read its processed data: {error}")
        return

    show_chart(completeness_chart(data["field_completeness"]))
    show_chart(publication_status_chart(data["publication_status"]))
    show_chart(geography_chart(data["geography"]))

    with st.expander("How to read this page"):
        st.markdown(
            "Publication place is inferred from the Publisher field. It does "
            "not describe the subject geography of a catalogue record. "
            "Publisher missing means that the source field is blank. Place "
            "unresolved means that Publisher text is present, but no reliable "
            "publication place could be identified."
        )

    if downloads is not None:
        downloads("page1", "Download Page 1 data")
