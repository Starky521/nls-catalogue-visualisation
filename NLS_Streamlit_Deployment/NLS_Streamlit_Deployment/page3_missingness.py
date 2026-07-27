from pathlib import Path
from typing import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


FLOW_COLUMNS = {
    "material_type",
    "period",
    "language_group",
    "date_status",
    "publisher_status",
    "place_result",
    "count",
}
EXAMPLE_COLUMNS = {
    "title",
    "date",
    "material_type",
    "period",
    "language",
    "language_group",
    "publisher_original",
    "date_status",
    "publisher_status",
    "place_result",
}

MATERIAL_ORDER = [
    "Notated music",
    "Sound recording",
    "Still image",
    "Software / multimedia",
    "Cartographic",
    "Moving image",
    "Text",
    "Other / not recorded",
]
PERIOD_ORDER = [
    "1600-1699",
    "1700-1799",
    "1800-1899",
    "1900-2020",
    "Date missing",
]
DATE_VALUES = ["Date present", "Date missing"]
PUBLISHER_VALUES = ["Publisher present", "Publisher missing"]
RESULT_VALUES = [
    "Place identified",
    "Place unresolved",
    "Explicitly unknown",
    "Ambiguous",
    "Not assessed (Publisher missing)",
]

MATERIAL_COLOURS = {
    "Notated music": "#796FA8",
    "Sound recording": "#7B8794",
    "Still image": "#C9A72E",
    "Software / multimedia": "#C875B0",
    "Cartographic": "#4F8A5B",
    "Moving image": "#D96C68",
    "Text": "#3B8EA5",
    "Other / not recorded": "#9A7B6C",
}
STATUS_COLOURS = {
    "Date present": "#2A7F78",
    "Date missing": "#C65D5D",
    "Publisher present": "#2A7F78",
    "Publisher missing": "#C65D5D",
    "Place identified": "#2A7F78",
    "Place unresolved": "#E39A35",
    "Explicitly unknown": "#6F5AA8",
    "Ambiguous": "#B58AC7",
    "Not assessed (Publisher missing)": "#9AA0A6",
}
DISPLAY_NAMES = {
    "title": "Title",
    "date": "Date",
    "material_type": "Material type",
    "period": "Period",
    "language": "Language",
    "publisher_original": "Original Publisher",
    "identified_place": "Identified place",
    "region": "Region",
    "place_result": "Publication-place result",
    "reason": "Rule used",
}
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
        "filename": "nls-metadata-pathways",
        "scale": 2,
    },
}


@st.cache_data(show_spinner=False)
def read_csv(path_text: str) -> pd.DataFrame:
    return pd.read_csv(Path(path_text))


def ordered_values(series: pd.Series, preferred: list[str]) -> list[str]:
    available = {
        value
        for value in series.dropna().astype(str).unique()
        if value.strip()
    }
    ordered = [value for value in preferred if value in available]
    ordered.extend(sorted(available - set(ordered)))
    return ordered


def load_and_validate(
    data_dir: Path,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    flow_path = data_dir / "alluvial_counts_full.csv"
    examples_path = data_dir / "record_examples.csv"
    missing = [
        path.name for path in (flow_path, examples_path) if not path.exists()
    ]
    if missing:
        st.error(
            "Page 3 cannot open because these processed files are missing: "
            + ", ".join(missing)
            + ". Upload the final Kaggle outputs to `data/page3`."
        )
        return None, None

    try:
        flow = read_csv(str(flow_path))
        examples = read_csv(str(examples_path))
    except Exception as error:
        st.error(f"Page 3 could not read its processed data: {error}")
        return None, None

    missing_flow = FLOW_COLUMNS - set(flow.columns)
    missing_examples = EXAMPLE_COLUMNS - set(examples.columns)
    if missing_flow or missing_examples:
        if missing_flow:
            st.error(
                "`alluvial_counts_full.csv` is missing: "
                + ", ".join(sorted(missing_flow))
            )
        if missing_examples:
            st.error(
                "`record_examples.csv` is missing: "
                + ", ".join(sorted(missing_examples))
            )
        return None, None

    flow = flow.copy()
    flow["count"] = pd.to_numeric(flow["count"], errors="coerce")
    if flow["count"].isna().any() or flow["count"].lt(0).any():
        st.error("The Page 3 count column contains invalid values.")
        return None, None

    invalid_labels = {
        "date_status": set(flow["date_status"].dropna()) - set(DATE_VALUES),
        "publisher_status": (
            set(flow["publisher_status"].dropna()) - set(PUBLISHER_VALUES)
        ),
        "place_result": set(flow["place_result"].dropna()) - set(RESULT_VALUES),
    }
    invalid_labels = {
        column: values for column, values in invalid_labels.items() if values
    }
    if invalid_labels:
        details = "; ".join(
            f"{column}: {', '.join(sorted(values))}"
            for column, values in invalid_labels.items()
        )
        st.error("Page 3 contains unexpected category labels. " + details)
        return None, None

    required_dimensions = [
        "material_type",
        "period",
        "language_group",
        "date_status",
        "publisher_status",
        "place_result",
    ]
    if flow[required_dimensions].isna().any().any():
        st.error("A Page 3 pathway contains a blank category.")
        return None, None
    if flow.duplicated(required_dimensions).any():
        st.error("Page 3 contains duplicate complete pathways.")
        return None, None

    bad_missing = (
        flow["publisher_status"].eq("Publisher missing")
        & ~flow["place_result"].eq("Not assessed (Publisher missing)")
    )
    bad_present = (
        flow["publisher_status"].eq("Publisher present")
        & flow["place_result"].eq("Not assessed (Publisher missing)")
    )
    if bad_missing.any() or bad_present.any():
        affected = int(flow.loc[bad_missing | bad_present, "count"].sum())
        st.error(
            f"Publisher-to-result validation failed for {affected:,} records. "
            "The chart has not been drawn."
        )
        return None, None

    return flow, examples


def apply_filters(
    data: pd.DataFrame,
    material_type: str,
    period: str,
    language_group: str,
) -> pd.DataFrame:
    filtered = data
    if material_type != "All material types":
        filtered = filtered.loc[
            filtered["material_type"].astype(str).eq(material_type)
        ]
    if period != "All periods":
        filtered = filtered.loc[filtered["period"].astype(str).eq(period)]
    if language_group != "All language groups":
        filtered = filtered.loc[
            filtered["language_group"].astype(str).eq(language_group)
        ]
    return filtered.copy()


def rgba(hex_colour: str, alpha: float) -> str:
    colour = hex_colour.lstrip("#")
    red, green, blue = (
        int(colour[index:index + 2], 16) for index in (0, 2, 4)
    )
    return f"rgba({red},{green},{blue},{alpha})"


def percentage(value: float, total: float) -> float:
    return 0.0 if total == 0 else value / total * 100


def format_count(value: float) -> str:
    return f"{int(round(value)):,}"


def prepare_chart_paths(
    filtered: pd.DataFrame,
    view: str,
) -> tuple[pd.DataFrame, float]:
    paths = (
        filtered.groupby(
            [
                "material_type",
                "date_status",
                "publisher_status",
                "place_result",
            ],
            observed=True,
            as_index=False,
        )["count"]
        .sum()
    )
    if view == "Percentage":
        type_totals = paths.groupby(
            "material_type", observed=True
        )["count"].transform("sum")
        paths["chart_value"] = paths["count"] / type_totals * 100
    else:
        paths["chart_value"] = paths["count"].astype(float)
    return paths, float(paths["chart_value"].sum())


def build_stage_links(
    paths: pd.DataFrame,
    source_column: str,
    target_column: str,
) -> pd.DataFrame:
    return (
        paths.groupby(
            [source_column, target_column],
            observed=True,
            as_index=False,
        )[["count", "chart_value"]]
        .sum()
    )


def build_sankey(
    filtered: pd.DataFrame,
    view: str,
) -> go.Figure:
    paths, chart_total = prepare_chart_paths(filtered, view)
    materials = ordered_values(paths["material_type"], MATERIAL_ORDER)
    active_dates = ordered_values(paths["date_status"], DATE_VALUES)
    active_publishers = ordered_values(
        paths["publisher_status"], PUBLISHER_VALUES
    )
    active_results = ordered_values(paths["place_result"], RESULT_VALUES)
    labels = materials + active_dates + active_publishers + active_results
    index = {label: position for position, label in enumerate(labels)}

    links = [
        (
            build_stage_links(paths, "material_type", "date_status"),
            "material_type",
            "date_status",
            "material",
        ),
        (
            build_stage_links(paths, "date_status", "publisher_status"),
            "date_status",
            "publisher_status",
            "date",
        ),
        (
            build_stage_links(paths, "publisher_status", "place_result"),
            "publisher_status",
            "place_result",
            "result",
        ),
    ]

    sources: list[int] = []
    targets: list[int] = []
    values: list[float] = []
    colours: list[str] = []
    customdata: list[list[str]] = []
    for table, source_column, target_column, colour_stage in links:
        for row in table.itertuples(index=False):
            source = getattr(row, source_column)
            target = getattr(row, target_column)
            raw_count = float(row.count)
            chart_value = float(row.chart_value)
            sources.append(index[source])
            targets.append(index[target])
            values.append(chart_value)
            if colour_stage == "material":
                colour = MATERIAL_COLOURS.get(source, "#7B8794")
            elif colour_stage == "date":
                colour = STATUS_COLOURS[source]
            else:
                colour = STATUS_COLOURS[target]
            colours.append(rgba(colour, 0.43))
            customdata.append([
                source,
                target,
                format_count(raw_count),
                f"{percentage(chart_value, chart_total):.1f}%",
            ])

    raw_total = float(paths["count"].sum())
    node_raw_totals: dict[str, float] = {}
    node_chart_totals: dict[str, float] = {}
    for column in [
        "material_type",
        "date_status",
        "publisher_status",
        "place_result",
    ]:
        raw = paths.groupby(column, observed=True)["count"].sum()
        chart = paths.groupby(column, observed=True)["chart_value"].sum()
        node_raw_totals.update(raw.to_dict())
        node_chart_totals.update(chart.to_dict())

    node_custom = [
        [
            format_count(node_raw_totals.get(label, 0)),
            f"{percentage(node_chart_totals.get(label, 0), chart_total):.1f}%",
        ]
        for label in labels
    ]
    node_colours = [
        MATERIAL_COLOURS.get(label, STATUS_COLOURS.get(label, "#7B8794"))
        for label in labels
    ]

    figure = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=labels,
                color=node_colours,
                pad=18,
                thickness=17,
                line=dict(color="rgba(36,39,43,.35)", width=0.7),
                customdata=node_custom,
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Records: %{customdata[0]}<br>"
                    "Part of displayed flow: %{customdata[1]}"
                    "<extra></extra>"
                ),
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colours,
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]} → %{customdata[1]}</b><br>"
                    "Records: %{customdata[2]}<br>"
                    "Part of displayed flow: %{customdata[3]}"
                    "<extra></extra>"
                ),
            ),
        )
    )
    figure.update_layout(
        height=690,
        margin=dict(l=25, r=185, t=55, b=35),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=12, color="#24272B"),
        annotations=[
            dict(x=0.00, y=1.06, xref="paper", yref="paper",
                 text="Material type", showarrow=False, xanchor="left"),
            dict(x=0.34, y=1.06, xref="paper", yref="paper",
                 text="Date information", showarrow=False),
            dict(x=0.67, y=1.06, xref="paper", yref="paper",
                 text="Publisher information", showarrow=False),
            dict(x=1.00, y=1.06, xref="paper", yref="paper",
                 text="Publication-place result",
                 showarrow=False, xanchor="right"),
        ],
    )
    return figure


def result_totals(flow: pd.DataFrame) -> dict[str, float]:
    totals = (
        flow.groupby("place_result", observed=True)["count"].sum().to_dict()
    )
    return {result: float(totals.get(result, 0)) for result in RESULT_VALUES}


def finding_text(flow: pd.DataFrame) -> str:
    total = float(flow["count"].sum())
    both_missing = float(
        flow.loc[
            flow["date_status"].eq("Date missing")
            & flow["publisher_status"].eq("Publisher missing"),
            "count",
        ].sum()
    )
    publisher_missing = float(
        flow.loc[
            flow["publisher_status"].eq("Publisher missing"), "count"
        ].sum()
    )
    unresolved = float(
        flow.loc[flow["place_result"].eq("Place unresolved"), "count"].sum()
    )
    return (
        f"Date and Publisher information are both missing in "
        f"{percentage(both_missing, total):.1f}% of the filtered records. "
        f"Publisher information is missing in "
        f"{percentage(publisher_missing, total):.1f}%. A further "
        f"{percentage(unresolved, total):.1f}% contain Publisher text, but "
        "their publication place could not be identified reliably."
    )


def filter_examples(
    examples: pd.DataFrame,
    material_type: str,
    period: str,
    language_group: str,
    result: str,
) -> pd.DataFrame:
    filtered = apply_filters(
        examples, material_type, period, language_group
    )
    filtered = filtered.loc[filtered["place_result"].astype(str).eq(result)]
    sort_columns = [
        column for column in ["title", "date", "publisher_original"]
        if column in filtered.columns
    ]
    if sort_columns:
        filtered = filtered.sort_values(
            sort_columns, kind="stable", na_position="last"
        )
    return filtered.head(20).copy()


def display_examples(examples: pd.DataFrame) -> None:
    preferred = [
        "title",
        "date",
        "material_type",
        "period",
        "language",
        "publisher_original",
        "identified_place",
        "region",
        "place_result",
        "reason",
    ]
    columns = [column for column in preferred if column in examples.columns]
    table = examples[columns].copy()
    for column in table.columns:
        if table[column].dtype == object:
            table[column] = table[column].replace(r"^\s*$", pd.NA, regex=True)
            table[column] = table[column].fillna("Not recorded")
    table = table.rename(columns=DISPLAY_NAMES)
    column_config = {}
    if "Title" in table:
        column_config["Title"] = st.column_config.TextColumn(
            "Title", width="large"
        )
    if "Original Publisher" in table:
        column_config["Original Publisher"] = st.column_config.TextColumn(
            "Original Publisher", width="large"
        )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


def render_page3(
    data_dir: Path,
    downloads: Callable[[str, str], None] | None = None,
) -> None:
    # EDITABLE PAGE 3 TEXT: change the title and introduction below.
    st.title("Missing information and publication-place results")
    st.markdown(
        """
        <p class="page-intro">
        Follow catalogue records from material type to Date information,
        Publisher information and the final publication-place result. The
        chart separates a blank Publisher field from Publisher text that is
        present but cannot be matched to a reliable place.
        </p>
        """,
        unsafe_allow_html=True,
    )

    flow, examples = load_and_validate(data_dir)
    if flow is None or examples is None:
        return

    filter_columns = st.columns(3)
    with filter_columns[0]:
        material_type = st.selectbox(
            "Material type",
            ["All material types"]
            + ordered_values(flow["material_type"], MATERIAL_ORDER),
            key="page3-material",
        )
    with filter_columns[1]:
        period = st.selectbox(
            "Publication period",
            ["All periods"] + ordered_values(flow["period"], PERIOD_ORDER),
            key="page3-period",
        )
    with filter_columns[2]:
        language_group = st.selectbox(
            "Language",
            ["All language groups"]
            + ordered_values(flow["language_group"], []),
            key="page3-language",
        )

    view = st.radio(
        "Flow width",
        ["Percentage", "Record count"],
        horizontal=True,
        key="page3-view",
        help=(
            "Percentage gives every displayed material type the same total "
            "width. Record count shows the true size of the catalogue."
        ),
    )
    filtered_flow = apply_filters(
        flow, material_type, period, language_group
    )
    total = float(filtered_flow["count"].sum())
    if filtered_flow.empty or total <= 0:
        st.info("No records match the current filters.")
        return

    results = result_totals(filtered_flow)
    both_missing = float(
        filtered_flow.loc[
            filtered_flow["date_status"].eq("Date missing")
            & filtered_flow["publisher_status"].eq("Publisher missing"),
            "count",
        ].sum()
    )
    metric_columns = st.columns(4)
    metric_columns[0].metric("Filtered records", format_count(total))
    metric_columns[1].metric(
        "Date and Publisher missing",
        format_count(both_missing),
        f"{percentage(both_missing, total):.1f}%",
        delta_color="off",
    )
    metric_columns[2].metric(
        "Place unresolved",
        format_count(results["Place unresolved"]),
        f"{percentage(results['Place unresolved'], total):.1f}%",
        delta_color="off",
    )
    metric_columns[3].metric(
        "Place identified",
        format_count(results["Place identified"]),
        f"{percentage(results['Place identified'], total):.1f}%",
        delta_color="off",
    )

    st.markdown(
        '<div class="section-label">1 · Metadata pathways</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Catalogue information from material type to place result")
    if view == "Percentage":
        st.caption(
            "Each displayed material type is normalised separately to 100%. "
            "Flow widths compare patterns within material types, not their "
            "total catalogue size."
        )
    else:
        st.caption(
            "Flow widths show the actual number of catalogue records. Text "
            "may dominate because it forms most of the catalogue."
        )
    st.plotly_chart(
        build_sankey(filtered_flow, view),
        use_container_width=True,
        config=PLOT_CONFIG,
    )
    st.info("**What the current view shows.** " + finding_text(filtered_flow))
    st.caption(
        "The chart shows combinations of metadata states. It does not show a "
        "causal process. Move the pointer over a block or connection to see "
        "the record count."
    )

    st.markdown(
        '<div class="section-label">2 · Catalogue record examples</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Records behind the selected result")
    st.markdown(
        "Choose a publication-place result to inspect representative records "
        "that also match the filters above."
    )
    example_result = st.selectbox(
        "Publication-place result",
        RESULT_VALUES,
        index=1,
        key="page3-example-result",
    )
    selected_examples = filter_examples(
        examples,
        material_type,
        period,
        language_group,
        example_result,
    )
    if selected_examples.empty:
        st.info("No saved examples match these filters and this result.")
    else:
        display_examples(selected_examples)

    with st.expander("Meaning of each publication-place result"):
        st.markdown(
            "**Place identified**  \n"
            "A publication place was identified reliably.\n\n"
            "**Place unresolved**  \n"
            "Publisher text is present, but no reliable publication place "
            "could be identified.\n\n"
            "**Explicitly unknown**  \n"
            "The record states that the publication place is unknown, for "
            "example `[S.l.]`.\n\n"
            "**Ambiguous**  \n"
            "A possible place name is present, but it cannot be assigned "
            "reliably to one location.\n\n"
            "**Not assessed (Publisher missing)**  \n"
            "The Publisher field is blank, so no publication-place assessment "
            "can be made."
        )

    if downloads is not None:
        downloads("page3", "Download Page 3 data")
