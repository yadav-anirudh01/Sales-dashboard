# Enterprise Business Dashboard — Quick Start

## What changed
- Switched the database from **MySQL** to **SQLite**. You don't need to install or
  configure any database server — a file called `business_analytics.db` is created
  automatically next to the script the first time you run it.
- Fixed a few bugs along the way (see "Fixes" below).

## How to run it

### 1. Install Python
You need Python 3.9 or newer. Check with:
```
python3 --version
```
If you don't have it, download from https://www.python.org/downloads/

### 2. Install the required packages
Open a terminal in this folder and run:
```
pip install -r requirements.txt
```
(On Windows, use `pip` or `py -m pip`; on Mac/Linux you may need `pip3`.)

### 3. Run the app
```
python3 sales_dashboard_app.py
```
(On Windows: `python sales_dashboard_app.py`)

A dark-themed desktop window titled **"Enterprise Business Dashboard Engine v2.5"**
should open. The database file is created automatically — there's nothing else to set up.

### 4. Add some data
Go to **Data Management** in the sidebar, fill out the form (date format is
`YYYY-MM-DD`, e.g. `2026-06-15`), and click **Commit Entry**. Once you have at least
5 records, the **Executive Dashboard** tab will show charts and AI-style insights.

## Fixes made to the original code
1. **Database**: MySQL connection (which required a local server, username, and
   password) replaced with a zero-config local SQLite file.
2. **Crash on empty data**: The dashboard chart no longer crashes when there are
   zero records — it now shows a friendly "no data yet" message instead.
3. **Form validation**: Adding a record with empty fields or non-numeric
   quantity/price now shows a clear error instead of an unhandled exception.
4. **Chart duplication bug**: Switching away from and back to the Dashboard tab
   no longer stacks duplicate charts on top of each other (memory leak fixed).
5. **Form doesn't clear**: After successfully adding a record, the input fields
   now clear automatically so you can add the next one without manually erasing.
6. **Date label overlap**: Rotated the x-axis date labels on the sales chart so
   they don't overlap when you have many data points.

## Notes
- Your data is saved in `business_analytics.db` in the same folder. Back this file
  up if you want to keep your sales history safe.
- To reset all data, simply delete `business_analytics.db` and restart the app —
  a fresh empty database will be created.
- The "AI Insights" panel is rule-based logic (not a live AI model) that looks at
  your sales trends — it requires at least 5 records to generate insights.
