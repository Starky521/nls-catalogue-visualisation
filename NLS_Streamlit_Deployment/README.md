# NLS Catalogue Visualisation

A two-page Streamlit site presenting interactive Plotly outputs from the
National Library of Scotland catalogue publication-place project.

## Pages

- **Catalogue Metadata Overview** — field completeness, publication-place
  metadata outcomes, and identified publication geography.
- **Publisher Relationships** — publication-place outcomes by material type,
  decade, and language, with a methodologically constrained Scotland focus.

The website reads only compact aggregate CSV files and prebuilt Plotly HTML. It
does not load the multi-million-row master Parquet dataset.

## Deploy without VS Code

1. Create a new GitHub repository.
2. Upload every file and folder from this project, preserving the structure.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/).
4. Choose **Create app** and select the GitHub repository.
5. Set the entrypoint to `streamlit_app.py`.
6. Deploy.

## Run locally (optional)

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Project structure

```text
streamlit_nls_site/
├── .streamlit/
│   └── config.toml
├── data/
│   ├── page1/
│   └── page2/
├── visuals/
│   ├── page1_overview.html
│   └── page2_relationships.html
├── streamlit_app.py
├── requirements.txt
└── README.md
```
