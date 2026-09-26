"""
Stage L v2: Advanced Question Analytics Dashboard
Generates a standalone HTML dashboard visualizing the extracted question database,
including topic frequency, marks distribution, and a searchable question table.
"""

import os
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "output", "question_database.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "output", "question_analytics_dashboard.html")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_question_data() -> pd.DataFrame:
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Question database not found at {INPUT_CSV}. Run stage_j_extractor.py first.")
    
    df = pd.read_csv(INPUT_CSV)
    # Clean and fill missing data
    df = df.fillna({
        "topic_mapping": "Unclassified",
        "confidence": 0.0,
        "estimated_marks": 1,
        "source_year": 0
    })
    # Ensure numeric types
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    df["estimated_marks"] = pd.to_numeric(df["estimated_marks"], errors="coerce").fillna(1)
    df["source_year"] = pd.to_numeric(df["source_year"], errors="coerce").fillna(0).astype(int)
    
    return df

def determine_confidence_severity(confidence: float) -> str:
    if confidence >= 0.6:
        return "success"
    elif confidence >= 0.3:
        return "warning"
    else:
        return "danger"

def generate_kpi_cards(df: pd.DataFrame) -> str:
    total_questions = len(df)
    avg_confidence = df["confidence"].mean() * 100
    unique_subjects = df["subject"].nunique()
    unique_years = df["source_year"].nunique()

    return f"""
    <div class="kpi-container">
        <div class="kpi-card primary">
            <h3>Total Questions Extracted</h3>
            <div class="kpi-value">{total_questions:,}</div>
        </div>
        <div class="kpi-card success">
            <h3>Avg. Topic Mapping Confidence</h3>
            <div class="kpi-value">{avg_confidence:.1f}%</div>
        </div>
        <div class="kpi-card warning">
            <h3>Subjects Covered</h3>
            <div class="kpi-value">{unique_subjects}</div>
        </div>
        <div class="kpi-card">
            <h3>Exam Years Represented</h3>
            <div class="kpi-value">{unique_years}</div>
        </div>
    </div>
    """

def generate_plotly_charts(df: pd.DataFrame) -> str:
    charts_html = ""
    
    # Chart 1: Topic Frequency Treemap (Hierarchical: Subject -> Topic)
    topic_counts = df.groupby(["subject", "topic_mapping"]).size().reset_index(name="count")
    fig1 = px.treemap(
        topic_counts, 
        path=[px.Constant("All Subjects"), "subject", "topic_mapping"], 
        values="count",
        title="Topic Frequency Distribution by Subject",
        color="count",
        color_continuous_scale="Blues"
    )
    fig1.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=400)
    charts_html += fig1.to_html(full_html=False, include_plotlyjs="cdn", default_width="100%")

    # Chart 2: Marks Distribution Bar Chart
    marks_counts = df.groupby(["subject", "estimated_marks"]).size().reset_index(name="count")
    fig2 = px.bar(
        marks_counts, 
        x="subject", 
        y="count", 
        color="estimated_marks",
        title="Question Count by Estimated Marks per Subject",
        labels={"count": "Number of Questions", "estimated_marks": "Marks", "subject": "Subject"},
        barmode="stack"
    )
    fig2.update_layout(margin=dict(t=40, b=20, l=40, r=20), height=400)
    charts_html += fig2.to_html(full_html=False, include_plotlyjs=False, default_width="100%")

    return charts_html

def generate_data_table(df: pd.DataFrame) -> str:
    # Sort by confidence descending to show best mappings first
    df_sorted = df.sort_values(by="confidence", ascending=False).head(500) # Limit to top 500 for browser performance
    
    rows_html = ""
    for _, row in df_sorted.iterrows():
        badge_class = determine_confidence_severity(row["confidence"])
        badge_text = f"{row['confidence']*100:.0f}%"
        
        # Truncate question text for table display
        q_text = row["question_text"]
        if len(q_text) > 150:
            q_text = q_text[:150] + "..."
            
        rows_html += f"""
        <tr>
            <td>{row['question_id']}</td>
            <td>{row['subject']}</td>
            <td>{row['source_year']}</td>
            <td>{row['topic_mapping']}</td>
            <td>{row['estimated_marks']}</td>
            <td><span class="badge {badge_class}">{badge_text}</span></td>
            <td class="question-text">{q_text}</td>
        </tr>
        """

    return f"""
    <table id="questionTable" class="display">
        <thead>
            <tr>
                <th>Q ID</th>
                <th>Subject</th>
                <th>Year</th>
                <th>Topic</th>
                <th>Marks</th>
                <th>Confidence</th>
                <th>Question Preview</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

def build_dashboard(df: pd.DataFrame) -> str:
    kpi_html = generate_kpi_cards(df)
    charts_html = generate_plotly_charts(df)
    table_html = generate_data_table(df)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISC Class XII Question Analytics Dashboard</title>
    
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    
    <style>
        :root {{
            --bg-color: #f4f6f9;
            --text-color: #333;
            --header-bg: #2c3e50;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #c0392b;
            --primary: #2980b9;
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

        .container {{ max-width: 1600px; margin: 20px auto; padding: 0 20px; }}
        
        .kpi-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .kpi-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #ccc; }}
        .kpi-card.primary {{ border-top-color: var(--primary); }}
        .kpi-card.success {{ border-top-color: var(--success); }}
        .kpi-card.warning {{ border-top-color: var(--warning); }}
        .kpi-card h3 {{ margin: 0 0 10px 0; font-size: 0.9rem; color: #666; text-transform: uppercase; }}
        .kpi-card .kpi-value {{ font-size: 2rem; font-weight: bold; color: #333; }}

        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(600px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}

        .table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow-x: auto; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; color: white; }}
        .badge.success {{ background-color: var(--success); }}
        .badge.warning {{ background-color: var(--warning); }}
        .badge.danger {{ background-color: var(--danger); }}
        
        .question-text {{ font-size: 0.9rem; color: #555; max-width: 400px; }}
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter {{ margin-bottom: 15px; }}
    </style>
</head>
<body>

    <div class="sticky-banner">
        <h1>📊 ISC Class XII Question Analytics Dashboard</h1>
        <span class="date">Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</span>
    </div>

    <div class="container">
        {kpi_html}
        
        <div class="charts-grid">
            <div class="chart-box">{charts_html.split('</div>')[0]}</div>
            <div class="chart-box">{charts_html.split('</div>')[1]}</div>
        </div>

        <div class="table-container">
            <h2 style="margin-top: 0;">Extracted Question Database (Top 500 by Confidence)</h2>
            <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                Use the search box to filter by subject, topic, or keyword. Sort by clicking column headers.
            </p>
            {table_html}
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script>
        $(document).ready(function() {{
            $('#questionTable').DataTable({{
                "pageLength": 15,
                "order": [[ 5, "desc" ]], // Sort by confidence descending
                "columnDefs": [
                    {{ "width": "10%", "targets": [0, 1, 2, 3, 4, 5] }},
                    {{ "width": "40%", "targets": [6] }}
                ]
            }});
        }});
    </script>
</body>
</html>
    """
    return html_template

def main():
    logging.info("Loading question database...")
    try:
        df = load_question_data()
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return

    logging.info("Generating advanced dashboard HTML...")
    html_content = build_dashboard(df)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    logging.info(f"Dashboard successfully generated: {OUTPUT_HTML}")
    logging.info("Open this file in any web browser to view the interactive analytics.")

if __name__ == "__main__":
    main()