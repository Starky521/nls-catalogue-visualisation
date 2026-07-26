# NLS Catalogue Visualisation

A three-page Streamlit site presenting interactive analysis of publication-place
metadata in the National Library of Scotland catalogue.

## Pages

- **Catalogue overview** — field completeness, publication-place results and
  identified publication geography.
- **Publication-place patterns** — results by material type, decade and
  language.
- **Missingness and uncertainty** — an interactive four-stage pathway chart
  linking material type, Date information, Publisher information and the final
  publication-place result.

The website reads processed CSV files rather than the five-million-row master
Parquet dataset.

## Page 3 data

Page 3 reads these files from `data/page3`:

- `alluvial_counts_full.csv` — complete pathway counts, including period and
  language groups for filtering.
- `record_examples.csv` — deterministic representative catalogue records.

The folder also contains the two small RAWGraphs experiment files:

- `rawgraphs_alluvial_percentage.csv`
- `rawgraphs_alluvial_count.csv`

The full research data keeps `Explicitly unknown` and `Ambiguous` separate.
`Not assessed (Publisher missing)` is used only when the Publisher field is
blank.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Project structure

```text
NLS_Streamlit_Deployment/
├── data/
│   ├── page1/
│   ├── page2/
│   └── page3/
├── visuals/
├── page2_dashboard.py
├── page3_missingness.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```
