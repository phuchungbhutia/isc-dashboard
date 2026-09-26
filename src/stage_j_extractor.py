"""
Stage J: Syllabus Mapping & Question Extraction (v2 - Robust Parsing)
Parses extracted .txt files from ISC papers to isolate questions, 
estimate marks, and map them to broad syllabus topics.
"""

import os
import re
import json
import csv
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "extractor.log")),
        logging.StreamHandler()
    ]
)

@dataclass
class QuestionRecord:
    question_id: str
    source_document: str
    source_year: int
    subject: str
    question_number: str
    question_text: str
    estimated_marks: int
    topic_mapping: str
    confidence: float
    extraction_warnings: List[str]

# --- Topic Mapping Heuristics ---
TOPIC_KEYWORDS = {
    "Physics": {
        "Electrostatics": ["electric field", "potential", "capacitor", "dipole", "gauss"],
        "Current Electricity": ["ohm's law", "kirchhoff", "potentiometer", "meter bridge", "drift"],
        "Magnetism": ["magnetic field", "biot-savart", "ampere", "lorentz", "galvanometer"],
        "Optics": ["prism", "lens", "mirror", "refraction", "diffraction", "interference", "young"],
        "Modern Physics": ["photoelectric", "bohr", "nuclear", "radioactivity", "de-broglie"],
        "Semiconductors": ["diode", "transistor", "logic gate", "p-n junction", "rectifier"]
    },
    "Chemistry": {
        "Solutions": ["osmotic", "freezing point", "boiling point", "raoult's law", "colligative"],
        "Electrochemistry": ["emf", "conductance", "faraday", "galvanic", "electrolytic", "nernst"],
        "Chemical Kinetics": ["rate", "order", "half-life", "activation energy", "arrhenius"],
        "Organic Chemistry": ["iupac", "mechanism", "aldehyde", "ketone", "amine", "phenol", "grignard"],
        "Coordination Compounds": ["ligand", "complex", "coordination number", "crystal field", "isomerism"],
        "Biomolecules": ["protein", "carbohydrate", "vitamin", "enzyme", "glucose"]
    },
    "Mathematics": {
        "Relations & Functions": ["function", "relation", "invertible", "domain", "range"],
        "Calculus": ["derivative", "integral", "differential equation", "continuity", "tangent"],
        "Algebra": ["matrix", "determinant", "vector", "probability", "linear programming"],
        "Coordinate Geometry": ["line", "circle", "conic", "parabola", "ellipse", "hyperbola"]
    },
    "Biology": {
        "Reproduction": ["gamete", "fertilization", "embryo", "menstrual", "pollination"],
        "Genetics": ["mendel", "dna", "rna", "mutation", "inheritance", "chromosome"],
        "Evolution": ["darwin", "natural selection", "fossil", "homologous"],
        "Human Physiology": ["heart", "brain", "kidney", "hormone", "digestion", "respiration"],
        "Biotechnology": ["pcr", "recombinant", "plasmid", "gel electrophoresis"]
    },
    "Computer Science": {
        "OOP & Java": ["class", "object", "inheritance", "polymorphism", "constructor", "array"],
        "Data Structures": ["stack", "queue", "linked list", "binary tree", "recursion"],
        "Boolean Algebra": ["k-map", "truth table", "logic gate", "minterm", "maxterm"],
        "Algorithms": ["complexity", "sorting", "searching", "big-o"]
    }
}

def infer_topic(subject: str, text: str) -> tuple[str, float]:
    """Heuristic topic mapping based on keyword matching."""
    text_lower = text.lower()
    subject_keywords = TOPIC_KEYWORDS.get(subject, {})
    
    best_topic = "General / Unclassified"
    max_matches = 0
    
    for topic, keywords in subject_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > max_matches:
            max_matches = matches
            best_topic = topic
            
    confidence = min(max_matches / 3.0, 1.0)
    return best_topic, round(confidence, 2)

def parse_marks(mark_str: str) -> int:
    """Safely parse marks from strings like '2', '4x2', '1x5=5'."""
    try:
        if '=' in mark_str:
            return int(mark_str.split('=')[-1].strip())
        elif 'x' in mark_str.lower():
            return int(mark_str.split('x')[-1].strip())
        else:
            return int(mark_str.strip())
    except (ValueError, IndexError):
        return 1 # Default fallback

def extract_questions_from_text(filepath: str, subject: str, year: int) -> List[QuestionRecord]:
    """Parse a .txt file and extract structured question records."""
    filename = os.path.basename(filepath)
    questions = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Failed to read {filename}: {e}")
        return questions

    # Split by double newlines to get logical blocks
    raw_blocks = re.split(r'\n\s*\n', content)
    
    # Matches marks: "[1]", "[2]", "[4x2]", "[1x5=5]"
    marks_pattern = re.compile(r'\[(\d+(?:\s*x\s*\d+)?(?:\s*=\s*\d+)?)\]')

    q_counter = 1
    for block in raw_blocks:
        block = block.strip()
        if len(block) < 30: # Ignore very short blocks (likely headers/footers)
            continue
            
        marks_match = marks_pattern.search(block)
        est_marks = parse_marks(marks_match.group(1)) if marks_match else 1
        
        # Clean up text (remove excessive whitespace)
        clean_text = re.sub(r'\s+', ' ', block).strip()
        
        # Infer topic
        topic, confidence = infer_topic(subject, clean_text)
        
        # Generate ID
        q_id = f"{subject.replace(' ', '')}_{year}_{q_counter:03d}"
        
        questions.append(QuestionRecord(
            question_id=q_id,
            source_document=filename,
            source_year=year,
            subject=subject,
            question_number=str(q_counter),
            question_text=clean_text[:500] + "..." if len(clean_text) > 500 else clean_text,
            estimated_marks=est_marks,
            topic_mapping=topic,
            confidence=confidence,
            extraction_warnings=[] if confidence > 0.3 else ["Low confidence topic mapping"]
        ))
        q_counter += 1
        
        # Limit to first 50 questions per file to prevent massive output bloat
        if q_counter > 50:
            questions[-1].extraction_warnings.append("Truncated at 50 questions per file limit.")
            break

    return questions

def main():
    logging.info("Starting Stage J: Question Extraction & Syllabus Mapping...")
    
    all_questions = []
    txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.txt')]
    
    if not txt_files:
        logging.error("No .txt files found in downloads/. Run the download pipeline first.")
        return

    for txt_file in txt_files:
        # Robust filename parsing
        year_match = re.search(r'(\d{4})', txt_file)
        year = int(year_match.group(1)) if year_match else 0
        
        filename_lower = txt_file.lower()
        if 'physics' in filename_lower: subject = 'Physics'
        elif 'chemistry' in filename_lower: subject = 'Chemistry'
        elif 'mathematics' in filename_lower or 'math' in filename_lower: subject = 'Mathematics'
        elif 'biology' in filename_lower: subject = 'Biology'
        elif 'computer' in filename_lower: subject = 'Computer Science'
        else: subject = 'Unknown'
            
        logging.info(f"Parsing: {txt_file} (Subject: {subject}, Year: {year})")
        filepath = os.path.join(DOWNLOAD_DIR, txt_file)
        
        extracted = extract_questions_from_text(filepath, subject, year)
        all_questions.extend(extracted)
        logging.info(f"  -> Extracted {len(extracted)} question blocks.")

    # Export to JSON
    json_path = os.path.join(OUTPUT_DIR, "question_database.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(q) for q in all_questions], f, indent=2)
        
    # Export to CSV
    csv_path = os.path.join(OUTPUT_DIR, "question_database.csv")
    if all_questions:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(all_questions[0]).keys())
            writer.writeheader()
            for q in all_questions:
                writer.writerow(asdict(q))
                
    logging.info(f"✅ Extraction complete. {len(all_questions)} questions saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()