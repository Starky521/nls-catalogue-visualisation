from pathlib import Path
from typing import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ORDER = [
    "Place identified",
    "Place unresolved",
    "Publisher missing",
    "Unknown / ambiguous",
]
LABEL = {
    "Place identified": "Place identified",
    "Place unresolved": "Place unresolved",
    "Publisher missing": "Publisher missing",
    "Unknown / ambiguous": "Explicitly unknown / ambiguous",
}
COLOUR = {
    "Place identified": "#247B78",
    "Place unresolved": "#D99031",
    "Publisher missing": "#C45B5B",
    "Unknown / ambiguous": "#8064A2",
}
SCOTLAND = "#3D7F5F"
GRID = "#E7E8EA"
INK = "#24272B"
PLOT_CONFIG = {"displayModeBar": False}


@st.cache_data(show_spinner=False)
def load_data(folder_text: str) -> dict[str, pd.DataFrame]:
    folder = Path(folder_text)
    return {path.stem: pd.read_csv(path) for path in sorted(folder.glob("*.csv"))}


def passed(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def layout(
    fig: go.Figure,
    height: int,
    left: int = 130,
    right: int = 90,
    bottom: int = 90,
) -> go.Figure:
    fig.update_layout(
        title=None,
        height=height,
        margin=dict(l=left, r=right, t=20, b=bottom),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=13, color=INK),
        hoverlabel=dict(font_size=13),
        legend=dict(
            orientation="h", yanchor="top", y=-0.18,
            xanchor="left", x=0, traceorder="normal",
        ),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    return fig


def selector(key: str) -> str:
    options = {}
    if key not in st.session_state:
        options["default"] = "All catalogue"
    return st.segmented_control(
        "View",
        ["All catalogue", "Scotland focus"],
        key=key,
        label_visibility="collapsed",
        **options,
    )


def begin_section(
    label: str,
    key: str,
    all_title: str,
    scotland_title: str,
    all_description: str,
    scotland_description: str,
) -> str:
    current = st.session_state.get(key, "All catalogue")
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.subheader(all_title if current == "All catalogue" else scotland_title)
    current = selector(key)
    st.markdown(
        all_description if current == "All catalogue" else scotland_description
    )
    return current


def plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


def all_type(data: pd.DataFrame) -> go.Figure:
    types = [
        "text", "cartographic", "moving image", "still image",
        "software/multimedia", "sound recording", "notated music",
    ]
    fig = go.Figure()
    for outcome in ORDER:
        current = (
            data.loc[data["outcome"].eq(outcome)]
            .set_index("document_type")
            .reindex(types)
        )
        values = current["percentage_within_type"]
        fig.add_bar(
            name=LABEL[outcome],
            y=types,
            x=values,
            orientation="h",
            marker_color=COLOUR[outcome],
            customdata=current[["count", "total_records_in_type"]].to_numpy(),
            text=[f"{value:.1f}%" if value >= 7 else "" for value in values],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="white"),
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"Status: {LABEL[outcome]}<br>"
                "Percentage: %{x:.1f}%<br>"
                "Record count: %{customdata[0]:,}<br>"
                "All records in this material type: %{customdata[1]:,}"
                "<extra>All catalogue</extra>"
            ),
        )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(
        title="Records within each material type (%)",
        range=[0, 100], ticksuffix="%",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=types[::-1])
    return layout(fig, 540, left=170, bottom=110)


def scotland_bars(
    data: pd.DataFrame,
    label_col: str,
    identified_col: str,
    axis_title: str,
    height: int,
) -> go.Figure:
    current = data.loc[passed(data["minimum_sample_passed"])].copy()
    current = current.sort_values("scotland_share_within_identified", ascending=False)
    labels = current[label_col]
    values = current["scotland_share_within_identified"]
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker_color=SCOTLAND,
            customdata=current[["scotland_count", identified_col]].to_numpy(),
            text=[f"{value:.1f}%" for value in values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Percentage identified as Scotland: %{x:.1f}%<br>"
                "Records identified as Scotland: %{customdata[0]:,}<br>"
                "All records with an identified place: %{customdata[1]:,}"
                "<extra>Scotland focus</extra>"
            ),
        )
    )
    fig.update_xaxes(
        title=axis_title,
        range=[0, max(10, float(values.max()) * 1.25)],
        ticksuffix="%",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=list(labels)[::-1])
    return layout(fig, height, left=170, right=115, bottom=90)


def all_decade(data: pd.DataFrame) -> go.Figure:
    current = data.loc[passed(data["minimum_sample_passed"])].copy()
    current["year"] = current["decade"].str[:4].astype(int)
    fig = go.Figure()
    for outcome in ORDER:
        subset = current.loc[current["outcome"].eq(outcome)].sort_values("year")
        fig.add_scatter(
            name=LABEL[outcome],
            x=subset["year"],
            y=subset["percentage_within_decade"],
            mode="lines",
            line=dict(color=COLOUR[outcome], width=2.5),
            customdata=subset[["decade", "count", "total_records_in_decade"]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                f"Status: {LABEL[outcome]}<br>"
                "Percentage: %{y:.1f}%<br>"
                "Record count: %{customdata[1]:,}<br>"
                "All dated records in this decade: %{customdata[2]:,}"
                "<extra>All catalogue</extra>"
            ),
        )
    ticks = list(range(1600, 2001, 50))
    fig.update_xaxes(
        title="Publication decade",
        tickmode="array",
        tickvals=ticks,
        ticktext=[f"{year}s" for year in ticks],
        tickangle=0,
    )
    fig.update_yaxes(
        title="Records within each decade (%)",
        range=[0, 100], ticksuffix="%",
    )
    return layout(fig, 520, left=100, bottom=115)


def scotland_decade(data: pd.DataFrame) -> go.Figure:
    current = data.loc[passed(data["minimum_sample_passed"])].copy()
    current["year"] = current["decade"].str[:4].astype(int)
    current = current.sort_values("year")
    fig = go.Figure(
        go.Scatter(
            x=current["year"],
            y=current["scotland_share_within_identified"],
            mode="lines+markers",
            line=dict(color=SCOTLAND, width=3),
            marker=dict(color=SCOTLAND, size=6),
            customdata=current[
                ["decade", "scotland_count", "identified_records_in_decade"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Percentage identified as Scotland: %{y:.1f}%<br>"
                "Records identified as Scotland: %{customdata[1]:,}<br>"
                "All records with an identified place: %{customdata[2]:,}"
                "<extra>Scotland focus</extra>"
            ),
        )
    )
    ticks = list(range(1600, 2001, 50))
    fig.update_xaxes(
        title="Publication decade",
        tickmode="array",
        tickvals=ticks,
        ticktext=[f"{year}s" for year in ticks],
        tickangle=0,
    )
    fig.update_yaxes(
        title="Records with a Scottish publication place (%)",
        rangemode="tozero", ticksuffix="%",
    )
    return layout(fig, 510, left=110, bottom=100)


def largest_languages(data: pd.DataFrame) -> list[str]:
    totals = (
        data[["language", "language_label", "total_records_in_language"]]
        .drop_duplicates()
        .sort_values("total_records_in_language", ascending=False)
    )
    return totals.head(12)["language"].tolist()


def all_language(data: pd.DataFrame, languages: list[str]) -> go.Figure:
    current = data.loc[data["language"].isin(languages)].copy()
    matrix = current.pivot(
        index="language", columns="outcome", values="percentage_within_language"
    )
    codes = (100 - matrix["Place identified"]).sort_values(ascending=False).index.tolist()
    names = (
        current[["language", "language_label"]]
        .drop_duplicates().set_index("language")["language_label"].to_dict()
    )
    labels = [names[code] for code in codes]
    fig = go.Figure()
    for outcome in ORDER:
        subset = current.loc[current["outcome"].eq(outcome)].set_index("language").reindex(codes)
        values = subset["percentage_within_language"]
        fig.add_bar(
            name=LABEL[outcome],
            y=labels,
            x=values,
            orientation="h",
            marker_color=COLOUR[outcome],
            customdata=subset[["count", "total_records_in_language"]].to_numpy(),
            text=[f"{value:.1f}%" if value >= 7 else "" for value in values],
            textposition="inside",
            textfont=dict(color="white"),
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"Status: {LABEL[outcome]}<br>"
                "Percentage: %{x:.1f}%<br>"
                "Record count: %{customdata[0]:,}<br>"
                "All records in this language: %{customdata[1]:,}"
                "<extra>All catalogue</extra>"
            ),
        )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(
        title="Records within each language group (%)",
        range=[0, 100], ticksuffix="%",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=labels[::-1])
    return layout(fig, 600, left=155, bottom=110)


def render_page2(data_dir: Path, downloads: Callable[[str, str], None]) -> None:
    data = load_data(str(data_dir))
    st.title("Publication-place Metadata Patterns")
    st.markdown(
        """
        <p class="page-intro">
        This page examines how publication-place information varies across
        different parts of the catalogue. The three sections compare records by
        material type, publication decade and language. Use <strong>All
        catalogue</strong> to examine identified, missing and uncertain
        publication-place information across the complete dataset. Use
        <strong>Scotland focus</strong> to examine records whose publication
        place was successfully identified as Scotland.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Scotland focus includes only records with an identified publication "
        "place. Records with missing, unresolved, explicitly unknown or ambiguous "
        "places cannot be assigned to Scotland and are therefore excluded from this view."
    )

    type_view = begin_section(
        "1 · Material type",
        "type-view",
        "How does publication-place status vary by material type?",
        "How does the percentage of records with a Scottish publication place vary by material type?",
        "For each material type, the chart shows the percentage of records "
        "whose publication place was identified, missing, unresolved or "
        "uncertain. Percentages are calculated separately within each material "
        "type. This allows material types with very different numbers of records "
        "to be compared.",
        "For each material type, this chart shows the percentage of records "
        "with an identified publication place that were classified as Scotland. "
        "Records with missing, unresolved, explicitly unknown or ambiguous places "
        "are excluded.",
    )
    if type_view == "All catalogue":
        plot(all_type(data["page2_type_all"]))
        st.info(
            "Publication-place status differs substantially by material type. "
            "Notated music and sound recordings have particularly high "
            "Publisher-missing percentages, while text, cartographic and "
            "moving-image records have higher place-identification percentages. "
            "Missingness is therefore not evenly distributed across the catalogue."
        )
    else:
        plot(scotland_bars(
            data["page2_type_scotland"],
            "document_type",
            "identified_records_in_type",
            "Records with a Scottish publication place (%)",
            520,
        ))
        st.info(
            "Scottish publication places are most common among moving-image and "
            "still-image records in this comparison. They are least common among "
            "notated-music records."
        )

    decade_view = begin_section(
        "2 · Decade",
        "decade-view",
        "How has publication-place status changed over time?",
        "How has the percentage of records with a Scottish publication place changed over time?",
        "The lines show the percentage of records assigned to each "
        "publication-place status within each decade. Only records with an "
        "extracted publication year are included. Decades with fewer than "
        "1,000 records are excluded to reduce the influence of very small samples.",
        "For each decade, the line shows the percentage of records with an "
        "identified publication place that were classified as Scotland. Only "
        "records with an extracted publication year are included. Decades with "
        "fewer than 1,000 identified records are excluded.",
    )
    if decade_view == "All catalogue":
        st.caption(
            "Records without an extracted publication year are not represented in "
            "this chart. The timeline therefore does not include the complete catalogue."
        )
        plot(all_decade(data["page2_decade_all"]))
        st.info(
            "The percentage of records with an identified publication place generally "
            "increases over time, while unresolved and uncertain records become less "
            "common. The earliest decades should be interpreted cautiously because "
            "they contain fewer records and reflect different historical cataloguing practices."
        )
    else:
        plot(scotland_decade(data["page2_decade_scotland"]))
        st.info(
            "The percentage changes substantially across the timeline. It reaches "
            "a marked peak during the early nineteenth century, falls during much "
            "of the twentieth century, and rises again in the later decades."
        )

    languages = largest_languages(data["page2_language_all"])
    language_view = begin_section(
        "3 · Language",
        "language-view",
        "Which language groups have more missing or unresolved publication-place information?",
        "How does the percentage of records with a Scottish publication place vary by language?",
        "For the largest named language groups, the visualisation shows the "
        "percentage of records with an identified place, a missing Publisher "
        "field, an unresolved place, or an explicitly unknown or ambiguous place. "
        "Percentages are calculated separately within each language group.",
        "For each language group, this chart shows the percentage of records "
        "with an identified publication place that were classified as Scotland. "
        "Missing, unresolved, explicitly unknown and ambiguous records are "
        "excluded. Only the largest named language groups are shown.",
    )
    if language_view == "All catalogue":
        plot(all_language(data["page2_language_all"], languages))
        st.info(
            "The difficulty of identifying a publication place varies considerably "
            "by language. For several language groups, unresolved Publisher text is "
            "more common than a blank Publisher field. This indicates that interpreting "
            "existing text can be a greater challenge than missing data alone."
        )
    else:
        current = data["page2_language_scotland"]
        current = current.loc[current["language"].isin(languages)]
        plot(scotland_bars(
            current,
            "language_label",
            "identified_records_in_language",
            "Records with a Scottish publication place (%)",
            590,
        ))
        st.info(
            "The highest percentages are shown for English and Polish records, "
            "followed by Latin. Most other language groups have much lower "
            "percentages of identified Scottish publication places."
        )

    downloads("page2", "Download Page 2 data")
