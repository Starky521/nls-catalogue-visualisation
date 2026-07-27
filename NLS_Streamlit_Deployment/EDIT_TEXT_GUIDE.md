# Editing website text directly on GitHub

All three live pages are now generated from small Python files. Open a file on
GitHub, select the pencil icon, edit the text and commit the change. Streamlit
will redeploy automatically.

## Page 1

File: `page1_overview.py`

Search for:

`EDITABLE PAGE 1 TEXT`

- `st.title("...")` is the page title.
- The text inside `<p class="page-intro"> ... </p>` is the introduction.
- Chart titles and subtitles are inside the functions
  `completeness_chart`, `publication_status_chart` and `geography_chart`.
- The method text is near the bottom inside
  `st.expander("How to read this page")`.

The old large `visuals/page1_overview.html` file is no longer used by the live
website.

## Page 2

File: `page2_dashboard.py`

Search for:

`EDITABLE PAGE 2 TEXT`

- `st.title("...")` is the page title.
- The text inside `<p class="page-intro"> ... </p>` is the introduction.
- Section titles and explanations are farther down in the same
  `render_page2` function.

The old `visuals/page2_relationships.html` file is not used by the live page.

## Page 3

File: `page3_missingness.py`

Search for:

`EDITABLE PAGE 3 TEXT`

- `st.title("...")` is the page title.
- The text inside `<p class="page-intro"> ... </p>` is the introduction.
- `st.subheader("...")` creates a section heading.
- `st.caption("...")` creates smaller explanatory text.
- The result definitions are near the bottom of `render_page3`.

## Sidebar and global font

File: `streamlit_app.py`

- Sidebar text appears below `st.sidebar`.
- The three navigation labels are inside `st.sidebar.radio`.
- Global font and heading styles are inside the `<style> ... </style>` block.

The global font is Arial. Main titles use the same 600 weight as the original
Page 1; other headings and normal interface text use regular weight.

## Safe GitHub editing process

1. Open the required `.py` file.
2. Select the pencil icon.
3. Change only text between quotation marks or HTML tags.
4. Keep quotation marks, commas, brackets and indentation.
5. Select **Commit changes**.
6. Wait for Streamlit to redeploy, then refresh the app.

For multi-line text, keep the opening and closing triple quotation marks:

```python
"""
Text can be edited here.
"""
```
