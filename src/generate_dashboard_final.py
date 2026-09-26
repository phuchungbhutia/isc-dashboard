import os
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CATALOG_CSV = os.path.join(OUTPUT_DIR, "isc_catalog.csv")
QUESTION_DB_CSV = os.path.join(OUTPUT_DIR, "question_database.csv")
PRACTICE_CSV = os.path.join(OUTPUT_DIR, "practice_questions.csv")
GAP_ANALYSIS_CSV = os.path.join(OUTPUT_DIR, "syllabus_gap_analysis.csv")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "isc_comprehensive_dashboard.html")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    dfs = {}
    for name, path in [("catalog", CATALOG_CSV), ("questions", QUESTION_DB_CSV), 
                       ("practice", PRACTICE_CSV), ("gap", GAP_ANALYSIS_CSV)]:
        if os.path.exists(path):
            dfs[name] = pd.read_csv(path)
            logging.info(f"✅ Loaded {name}: {len(dfs[name])} rows")
        else:
            logging.warning(f"⚠️ {name} not found at {path}")
            dfs[name] = None
    
    if dfs["questions"] is not None:
        dfs["questions"]["estimated_marks"] = pd.to_numeric(dfs["questions"]["estimated_marks"], errors="coerce").fillna(1)
        dfs["questions"]["confidence"] = pd.to_numeric(dfs["questions"]["confidence"], errors="coerce").fillna(0.0)
        
    return dfs

def generate_html(dfs):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # KPI Calculations
    kpis = []
    if dfs["catalog"] is not None:
        kpis.append(("Total Documents", len(dfs["catalog"]), "📄", "primary"))
        kpis.append(("Download Success", f"{(dfs['catalog']['download_status']=='success').mean()*100:.1f}%", "✅", "success"))
    if dfs["questions"] is not None:
        kpis.append(("Questions Extracted", f"{len(dfs['questions']):,}", "❓", "warning"))
        kpis.append(("Avg Confidence", f"{dfs['questions']['confidence'].mean()*100:.1f}%", "🎯", "info"))
    if dfs["gap"] is not None:
        kpis.append(("Syllabus Gaps", (dfs["gap"]["gap_status"]=="Gap Identified").sum(), "⚠️", "danger"))

    kpi_html = "".join([f'<div class="kpi-card {color}"><div class="kpi-icon">{icon}</div><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div></div>' for label, val, icon, color in kpis])

    # Charts
    charts_html = ""
    if dfs["questions"] is not None:
        topic_counts = dfs["questions"].groupby(['subject', 'topic_mapping']).size().reset_index(name='count')
        fig = px.treemap(topic_counts, path=[px.Constant('All'), 'subject', 'topic_mapping'], values='count', color='count', color_continuous_scale='Blues')
        fig.update_layout(height=500, margin=dict(t=50, l=25, r=25, b=25))
        charts_html += f'<div class="chart-container full-width">{fig.to_html(full_html=False, include_plotlyjs=False)}</div>'

    # Tables
    table_html = ""
    if dfs["questions"] is not None:
        table_html = '<div class="table-section"><h3>📋 Extracted Questions</h3><div class="table-controls"><input type="text" id="qSearch" placeholder="Search..."><select id="qSubject"><option value="">All</option>'
        for sub in dfs["questions"]["subject"].unique():
            table_html += f'<option value="{sub}">{sub}</option>'
        table_html += '</select></div><div class="table-container"><table class="data-table"><thead><tr><th>ID</th><th>Subject</th><th>Topic</th><th>Marks</th><th>Confidence</th><th>Preview</th></tr></thead><tbody>'
        for _, row in dfs["questions"].head(200).iterrows():
            conf = 'high' if row['confidence'] >= 0.6 else ('medium' if row['confidence'] >= 0.3 else 'low')
            preview = str(row['question_text'])[:120] + '...'
            table_html += f'<tr data-subject="{row["subject"]}"><td>{row["question_id"]}</td><td>{row["subject"]}</td><td>{row["topic_mapping"]}</td><td>{row["estimated_marks"]}</td><td><span class="badge {conf}">{row["confidence"]:.0%}</span></td><td class="q-text">{preview}</td></tr>'
        table_html += '</tbody></table></div></div>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISC Class XII Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .header h1 {{ color: #667eea; }}
        .section {{ background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .section h2 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .kpi-card {{ padding: 25px; border-radius: 15px; text-align: center; color: white; transition: transform 0.3s; }}
        .kpi-card:hover {{ transform: translateY(-5px); }}
        .kpi-card.primary {{ background: linear-gradient(135deg, #667eea, #764ba2); }}
        .kpi-card.success {{ background: linear-gradient(135deg, #11998e, #38ef7d); }}
        .kpi-card.warning {{ background: linear-gradient(135deg, #f093fb, #f5576c); }}
        .kpi-card.info {{ background: linear-gradient(135deg, #4facfe, #00f2fe); }}
        .kpi-card.danger {{ background: linear-gradient(135deg, #fa709a, #fee140); }}
        .kpi-icon {{ font-size: 2.5em; }}
        .kpi-value {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
        .kpi-label {{ font-size: 0.9em; text-transform: uppercase; opacity: 0.9; }}
        .chart-container {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .chart-container.full-width {{ grid-column: 1 / -1; }}
        .table-controls {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .table-controls input, .table-controls select {{ padding: 10px; border: 2px solid #ddd; border-radius: 8px; }}
        .data-table {{ width: 100%; border-collapse: collapse; }}
        .data-table thead {{ background: #667eea; color: white; position: sticky; top: 0; }}
        .data-table th, .data-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .data-table tbody tr:hover {{ background: #f8f9fa; }}
        .badge {{ padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }}
        .badge.high {{ background: #d4edda; color: #155724; }}
        .badge.medium {{ background: #fff3cd; color: #856404; }}
        .badge.low {{ background: #f8d7da; color: #721c24; }}
        .q-text {{ max-width: 400px; font-size: 0.9em; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ISC Class XII Analytics Dashboard</h1>
            <p>Generated: {timestamp} | Maintained by: phuchungbhutia</p>
        </div>
        <div class="section">
            <h2>📈 Executive Summary</h2>
            <div class="kpi-grid">{kpi_html}</div>
        </div>
        <div class="section">
            <h2>❓ Question Analytics</h2>
            <div class="chart-container full-width">{charts_html}</div>
        </div>
        <div class="section">
            {table_html}
        </div>
    </div>
    <script>
        document.getElementById('qSearch')?.addEventListener('input', function(e) {{
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.data-table tbody tr').forEach(row => {{
                row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
            }});
        }});
        document.getElementById('qSubject')?.addEventListener('change', function(e) {{
            const sub = e.target.value;
            document.querySelectorAll('.data-table tbody tr').forEach(row => {{
                row.style.display = (!sub || row.dataset.subject === sub) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    logging.info("Starting dashboard generation...")
    dfs = load_data()
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(generate_html(dfs))
    logging.info(f"✅ Dashboard saved to: {OUTPUT_HTML}")