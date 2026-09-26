"""
ISC Resource Library Interactive Dashboard Generator
Generates a standalone HTML dashboard with Plotly visualizations, 
sortable tables, and severity-based risk indicators.
"""

import os
import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "output", "isc_catalog.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "output", "isc_dashboard.html")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

@dataclass
class DashboardConfig:
    primary_color: str = "#1f77b4"
    success_color: str = "#2ca02c"
    warning_color: str = "#ff7f0e"
    danger_color: str = "#d62728"

def load_catalog() -> pd.DataFrame:
    """Load and validate the catalog CSV."""
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Catalog not found at {INPUT_CSV}. Run the extraction pipeline first.")
    
    df = pd.read_csv(INPUT_CSV)
    df = df.fillna({
        "extraction_method": "unknown",
        "download_status": "failed",
        "text_length": 0,
        "page_count": 0
    })
    return df

def determine_severity(row: pd.Series) -> str:
    """Assign severity-based risk indicators for UI styling."""
    if row["download_status"] != "success":
        return "danger"
    elif row["extraction_method"] == "ocr":
        return "warning"
    elif row["extraction_method"] == "native_text" and row["text_length"] > 1000:
        return "success"
    else:
        return "warning"

def generate_kpi_cards(df: pd.DataFrame) -> str:
    """Generate HTML for executive KPI cards."""
    total_docs = len(df)
    success_rate = (df["download_status"] == "success").mean() * 100
    native_text_pct = (df["extraction_method"] == "native_text").mean() * 100
    ocr_pct = (df["extraction_method"] == "ocr").mean() * 100

    return f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <h3>Total Documents</h3>
            <div class="kpi-value">{total_docs}</div>
        </div>
        <div class="kpi-card success">
            <h3>Download Success Rate</h3>
            <div class="kpi-value">{success_rate:.1f}%</div>
        </div>
        <div class="kpi-card primary">
            <h3>Native Text Extraction</h3>
            <div class="kpi-value">{native_text_pct:.1f}%</div>
        </div>
        <div class="kpi-card warning">
            <h3>Required OCR</h3>
            <div class="kpi-value">{ocr_pct:.1f}%</div>
        </div>
    </div>
    """

def generate_plotly_charts(df: pd.DataFrame) -> str:
    """Generate Plotly charts and return as HTML div strings."""
    charts_html = ""
    
    # Chart 1: Extraction Method Distribution
    method_counts = df["extraction_method"].value_counts().reset_index()
    method_counts.columns = ["Method", "Count"]
    fig1 = px.pie(
        method_counts, values="Count", names="Method",
        color="Method",
        color_discrete_map={"native_text": "#2ca02c", "ocr": "#ff7f0e", "failed": "#d62728", "unknown": "#9467bd"},
        title="Extraction Method Distribution"
    )
    fig1.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350)
    charts_html += fig1.to_html(full_html=False, include_plotlyjs="cdn", default_width="100%")

    # Chart 2: Text Length by Subject
    fig2 = px.box(
        df, x="subject", y="text_length", color="extraction_method",
        title="Extracted Text Length by Subject",
        labels={"text_length": "Character Count", "subject": "Subject"}
    )
    fig2.update_layout(margin=dict(t=40, b=20, l=40, r=20), height=350)
    charts_html += fig2.to_html(full_html=False, include_plotlyjs=False, default_width="100%")

    return charts_html

def generate_data_table(df: pd.DataFrame) -> str:
    """Generate a sortable, searchable HTML table with severity badges."""
    df["severity"] = df.apply(determine_severity, axis=1)
    
    display_df = df[["title", "subject", "year", "document_type", "extraction_method", "page_count", "text_length", "severity"]].copy()
    display_df.rename(columns={
        "title": "Document Title",
        "subject": "Subject",
        "year": "Year",
        "document_type": "Type",
        "extraction_method": "Extraction",
        "page_count": "Pages",
        "text_length": "Text Length"
    }, inplace=True)

    rows_html = ""
    for _, row in display_df.iterrows():
        badge_class = row["severity"]
        badge_text = row["severity"].upper()
        
        rows_html += f"""
        <tr>
            <td>{row['Document Title']}</td>
            <td>{row['Subject']}</td>
            <td>{row['Year']}</td>
            <td>{row['Type'].replace('_', ' ').title()}</td>
            <td>{row['Extraction'].replace('_', ' ').title()}</td>
            <td>{row['Pages']}</td>
            <td>{row['Text Length']:,}</td>
            <td><span class="badge {badge_class}">{badge_text}</span></td>
        </tr>
        """

    return f"""
    <table id="resourceTable" class="display">
        <thead>
            <tr>
                <th>Document Title</th>
                <th>Subject</th>
                <th>Year</th>
                <th>Type</th>
                <th>Extraction</th>
                <th>Pages</th>
                <th>Text Length</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

def build_dashboard(df: pd.DataFrame) -> str:
    """Assemble the complete standalone HTML dashboard."""
    kpi_html = generate_kpi_cards(df)
    charts_html = generate_plotly_charts(df)
    table_html = generate_data_table(df)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISC Class XII Resource Library Audit Dashboard</title>
    
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    
    <style>
        :root {{
            --bg-color: #f4f6f9;
            --text-color: #333;
            --header-bg: #1f77b4;
            --success: #2ca02c;
            --warning: #ff7f0e;
            --danger: #d62728;
        }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 0; }}
        
        .sticky-banner {{
            position: sticky; top: 0; z-index: 1000;
            background: var(--header-bg); color: white;
            padding: 15px 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: flex; justify-content: space-between; align-items: center;
        }}
        .sticky-banner h1 {{ margin: 0; font-size: 1.5rem; }}
        .sticky-banner .date {{ font-size: 0.9rem; opacity: 0.9; }}

        .container {{ max-width: 1400px; margin: 20px auto; padding: 0 20px; }}
        
        .kpi-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .kpi-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #ccc; }}
        .kpi-card.success {{ border-top-color: var(--success); }}
        .kpi-card.primary {{ border-top-color: var(--header-bg); }}
        .kpi-card.warning {{ border-top-color: var(--warning); }}
        .kpi-card h3 {{ margin: 0 0 10px 0; font-size: 0.9rem; color: #666; text-transform: uppercase; }}
        .kpi-card .kpi-value {{ font-size: 2rem; font-weight: bold; color: #333; }}

        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}

        .table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; color: white; }}
        .badge.success {{ background-color: var(--success); }}
        .badge.warning {{ background-color: var(--warning); }}
        .badge.danger {{ background-color: var(--danger); }}
        
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter {{ margin-bottom: 15px; }}
    </style>
</head>
<body>

    <div class="sticky-banner">
        <h1>📚 ISC Class XII Resource Library Audit</h1>
        <span class="date">Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</span>
    </div>

    <div class="container">
        {kpi_html}
        
        <div class="charts-grid">
            <div class="chart-box">{charts_html.split('</div>')[0]}</div>
            <div class="chart-box">{charts_html.split('</div>')[1]}</div>
        </div>

        <div class="table-container">
            <h2 style="margin-top: 0;">Document Catalog & Severity Audit</h2>
            {table_html}
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script>
        $(document).ready(function() {{
            $('#resourceTable').DataTable({{
                "pageLength": 10,
                "order": [[ 7, "asc" ]]
            }});
        }});
    </script>
</body>
</html>
    """
    return html_template

def main():
    logging.info("Loading catalog data...")
    try:
        df = load_catalog()
    except Exception as e:
        logging.error(f"Failed to load catalog: {e}")
        return

    logging.info("Generating dashboard HTML...")
    html_content = build_dashboard(df)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    logging.info(f"✅ Dashboard successfully generated: {OUTPUT_HTML}")
    logging.info("Open this file in any web browser to view the interactive dashboard.")

if __name__ == "__main__":
    main()