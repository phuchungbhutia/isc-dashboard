"""
Stage M: Syllabus Alignment & Gap Analysis
Maps extracted questions to the official CISCE ISC Class XII syllabus 
and identifies under-represented chapters (study gaps).
"""

import os
import json
import csv
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import pandas as pd

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "output", "question_database.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "output", "syllabus_gap_analysis.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "syllabus_gap_analysis.csv")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "gap_analyzer.log")),
        logging.StreamHandler()
    ]
)

# --- Official CISCE ISC Class XII Syllabus Structure ---
OFFICIAL_SYLLABUS = {
    "Physics": [
        "Electrostatics", "Current Electricity", "Magnetic Effects of Current & Magnetism", 
        "Electromagnetic Induction & Alternating Currents", "Electromagnetic Waves", 
        "Optics", "Dual Nature of Matter and Radiation", "Atoms and Nuclei", 
        "Electronic Devices (Semiconductors)", "Communication Systems"
    ],
    "Chemistry": [
        "Solid State", "Solutions", "Electrochemistry", "Chemical Kinetics", "Surface Chemistry",
        "p-Block Elements", "d- and f-Block Elements", "Coordination Compounds",
        "Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers", 
        "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules", 
        "Polymers", "Chemistry in Everyday Life"
    ],
    "Mathematics": [
        "Relations and Functions", "Inverse Trigonometric Functions", "Matrices", "Determinants",
        "Continuity and Differentiability", "Applications of Derivatives", "Integrals",
        "Applications of the Integrals", "Differential Equations", "Vector Algebra",
        "Three Dimensional Geometry", "Linear Programming", "Probability"
    ],
    "Biology": [
        "Reproduction in Organisms & Human Reproduction", "Sexual Reproduction in Flowering Plants",
        "Principles of Inheritance and Variation (Genetics)", "Molecular Basis of Inheritance",
        "Evolution", "Human Health and Disease", "Microbes in Human Welfare",
        "Biotechnology: Principles and Processes", "Biotechnology and its Applications",
        "Organisms and Populations", "Ecosystem", "Biodiversity and Conservation"
    ],
    "Computer Science": [
        "Java Programming & OOP Concepts", "Data Structures (Arrays, Strings)", 
        "Data Structures (Stacks, Queues, Linked Lists)", "Boolean Algebra & Logic Gates",
        "Computer Networks", "Database Management (SQL)"
    ]
}

@dataclass
class SyllabusCoverageRecord:
    subject: str
    official_chapter: str
    mapped_topics: List[str]
    total_questions: int
    total_marks: int
    coverage_score: float  # Normalized score based on max questions in that subject
    gap_status: str        # "Strong", "Adequate", "Gap Identified"
    recommended_action: str

def load_question_data() -> pd.DataFrame:
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Question database not found at {INPUT_CSV}.")
    df = pd.read_csv(INPUT_CSV)
    df = df.fillna({"topic_mapping": "Unclassified", "estimated_marks": 1})
    df["estimated_marks"] = pd.to_numeric(df["estimated_marks"], errors="coerce").fillna(1)
    return df

def map_topics_to_syllabus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps the heuristic 'topic_mapping' to the official CISCE chapters.
    Uses a simplified fuzzy-match approach based on the TOPIC_KEYWORDS from Stage J.
    """
    # Simplified mapping dictionary (Heuristic Topic -> Official Chapter)
    TOPIC_TO_CHAPTER = {
        "Electrostatics": "Electrostatics",
        "Current Electricity": "Current Electricity",
        "Magnetism": "Magnetic Effects of Current & Magnetism",
        "Optics": "Optics",
        "Modern Physics": "Dual Nature of Matter and Radiation", # Grouped for simplicity
        "Semiconductors": "Electronic Devices (Semiconductors)",
        "Solutions": "Solutions",
        "Electrochemistry": "Electrochemistry",
        "Chemical Kinetics": "Chemical Kinetics",
        "Organic Chemistry": "Aldehydes, Ketones and Carboxylic Acids", # Broad mapping
        "Coordination Compounds": "Coordination Compounds",
        "Biomolecules": "Biomolecules",
        "Relations & Functions": "Relations and Functions",
        "Calculus": "Continuity and Differentiability", # Broad mapping
        "Algebra": "Matrices", # Broad mapping
        "Coordinate Geometry": "Three Dimensional Geometry",
        "Reproduction": "Reproduction in Organisms & Human Reproduction",
        "Genetics": "Principles of Inheritance and Variation (Genetics)",
        "Evolution": "Evolution",
        "Human Physiology": "Human Health and Disease",
        "Biotechnology": "Biotechnology: Principles and Processes",
        "OOP & Java": "Java Programming & OOP Concepts",
        "Data Structures": "Data Structures (Stacks, Queues, Linked Lists)",
        "Boolean Algebra": "Boolean Algebra & Logic Gates",
        "Algorithms": "Computer Networks" # Fallback
    }
    
    df["official_chapter"] = df["topic_mapping"].map(TOPIC_TO_CHAPTER).fillna("Unclassified / General")
    return df

def analyze_gaps(df: pd.DataFrame) -> List[SyllabusCoverageRecord]:
    coverage_records = []
    
    for subject, chapters in OFFICIAL_SYLLABUS.items():
        subject_df = df[df["subject"] == subject]
        max_questions_in_subject = subject_df.groupby("official_chapter").size().max()
        if max_questions_in_subject == 0:
            max_questions_in_subject = 1 # Prevent division by zero
            
        for chapter in chapters:
            chapter_df = subject_df[subject_df["official_chapter"] == chapter]
            q_count = len(chapter_df)
            marks_count = chapter_df["estimated_marks"].sum()
            
            # Calculate coverage score (0.0 to 1.0)
            score = q_count / max_questions_in_subject if max_questions_in_subject > 0 else 0.0
            
            # Determine gap status
            if score >= 0.6:
                status = "Strong"
                action = "Focus on advanced problem-solving and previous year variations."
            elif score >= 0.2:
                status = "Adequate"
                action = "Review standard textbook examples and practice medium-difficulty questions."
            else:
                status = "Gap Identified"
                action = "URGENT: This chapter is under-represented. Study from official CISCE syllabus and generate targeted practice."
                
            # Get mapped heuristic topics for transparency
            mapped_topics = chapter_df["topic_mapping"].unique().tolist()
            
            coverage_records.append(SyllabusCoverageRecord(
                subject=subject,
                official_chapter=chapter,
                mapped_topics=mapped_topics,
                total_questions=q_count,
                total_marks=int(marks_count),
                coverage_score=round(score, 2),
                gap_status=status,
                recommended_action=action
            ))
            
    return coverage_records

def main():
    logging.info("Starting Stage M: Syllabus Alignment & Gap Analysis...")
    
    try:
        df = load_question_data()
        df = map_topics_to_syllabus(df)
    except Exception as e:
        logging.error(f"Failed to load/process data: {e}")
        return
        
    logging.info("Analyzing coverage against official CISCE syllabus...")
    coverage_records = analyze_gaps(df)
    
    # Export to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in coverage_records], f, indent=2)
        
    # Export to CSV
    if coverage_records:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(coverage_records[0]).keys())
            writer.writeheader()
            for r in coverage_records:
                writer.writerow(asdict(r))
                
    gaps = [r for r in coverage_records if r.gap_status == "Gap Identified"]
    logging.info(f"✅ Analysis complete. Identified {len(gaps)} syllabus chapters with coverage gaps.")
    logging.info(f"Saved detailed report to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()