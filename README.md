
# 📚 ISC Class XII Study Resource Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production--Ready-success)

An evidence-based, automated pipeline for discovering, downloading, extracting, analyzing, and visualizing ISC Class XII examination resources.

## 📊 Dashboard Widgets & Statistics

When you run the pipeline, the generated HTML dashboard includes:

| Widget | Description | Data Source |
|--------|-------------|-------------|
| **Total Documents** | Count of successfully downloaded PDFs | `isc_catalog.csv` |
| **Download Success** | Percentage of successful HTTP downloads | `isc_catalog.csv` |
| **Questions Extracted** | Total isolated question blocks parsed | `question_database.csv` |
| **Avg Confidence** | Mean accuracy of heuristic topic mapping | `question_database.csv` |
| **Syllabus Gaps** | Count of chapters with <20% coverage | `syllabus_gap_analysis.csv` |
| **Topic Treemap** | Hierarchical visualization of topic frequency | `question_database.csv` |

## 🏗️ File Structure

```text
isc-resource-pipeline/
├── .gitignore                  # Excludes venv, bin, downloads, logs
├── LICENSE                     # MIT License
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── src/                        # Source code
│   ├── download_and_process.py # Stage E-I: Download & Extract
│   ├── stage_j_extractor.py    # Stage J: Question Extraction
│   ├── stage_k_practice_generator.py # Stage K: Practice Questions
│   ├── stage_m_gap_analyzer.py # Stage M: Gap Analysis
│   └── generate_dashboard_final.py   # Stage L: Analytics Dashboard
├── data/                       # Data directory
│   ├── downloads/              # Raw PDFs and TXTs (gitignored)
│   ├── output/                 # Generated CSVs and HTML dashboard
│   └── logs/                   # Execution logs (gitignored)
└── bin/                        # Local OCR binaries (gitignored)
```
## ⚙️ Setup & Git Commands

### 1. Clone and Setup

```bash
git clone https://github.com/phuchungbhutia/isc-dashboard.git
cd isc-dashboard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
python src/generate_dashboard_final.py
```

### 3. Initialize Git (If starting fresh)

```bash
git init
git add .
git commit -m "Initial commit: ISC Resource Pipeline"
git branch -M main
git remote add origin https://github.com/phuchungbhutia/isc-dashboard.git
git push -u origin main
```

## 🌐 GitHub Pages Deployment

1. Push your code to the `main` branch.
2. Go to your repository on GitHub → **Settings** → **Pages**.
3. Under **Build and deployment** > **Source**, select **Deploy from a branch**.
4. Select Branch: `main` and Folder: `/ (root)`.
5. Click **Save**. Wait 1-2 minutes.
6. Your dashboard will be live at: `https://phuchungbhutia.github.io/isc-dashboard/data/output/isc_comprehensive_dashboard.html`

## 🐛 Troubleshooting

| Issue                                             | Solution                                                                                                         |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'pandas'` | Ensure your virtual environment is activated:`venv\Scripts\activate` then `pip install -r requirements.txt`. |
| `FileNotFoundError` for CSVs                    | Run`python src/generate_dashboard_final.py` first to generate the `data/output/` files.                      |
| Dashboard charts not loading                      | The HTML file requires an internet connection to load the Plotly.js library from the CDN.                        |
| Git rejects large files                           | Ensure`data/downloads/` and `bin/` are listed in your `.gitignore` file.                                   |

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### 🎯 Final Dashboard URL

Your interactive dashboard will be publicly accessible at:

```text
https://phuchungbhutia.github.io/isc-dashboard/data/output/isc_comprehensive_dashboard.html
```

---

*Built with ❤️ by phuchungbhutia for ISC students and educators.*


---