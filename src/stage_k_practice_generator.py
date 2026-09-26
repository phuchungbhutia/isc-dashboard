"""
Stage K: Evidence-Based Practice Question Generation
Analyzes the extracted question database to synthesize original, 
syllabus-aligned practice questions with answer outlines.
"""

import os
import json
import csv
import logging
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import pandas as pd

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "output", "question_database.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "output", "practice_questions.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "practice_questions.csv")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "generator.log")),
        logging.StreamHandler()
    ]
)

@dataclass
class PracticeQuestion:
    practice_question_id: str
    question: str
    subject: str
    chapter: str
    topic: str
    question_type: str
    marks: int
    difficulty: str
    source_basis: List[str]
    reason_for_inclusion: str
    not_a_prediction: bool
    answer_outline: str
    verification_notes: List[str]

# --- ISC-Style Question Templates for Concept Synthesis ---
TEMPLATES = {
    "Physics": [
        "Derive an expression for {concept_a} and explain how it is affected if {concept_b} is doubled.",
        "State the principle of {concept_a}. Using a labelled diagram, explain its application in {concept_b}.",
        "A {concept_a} is connected to a {concept_b}. Calculate the {concept_c} and discuss two sources of error in this measurement."
    ],
    "Chemistry": [
        "Give a reasoned explanation for why {concept_a} exhibits {concept_b}, whereas {concept_c} does not.",
        "Write the balanced chemical equation for the conversion of {concept_a} to {concept_b}. Name the reagent used.",
        "Define {concept_a}. How does the addition of {concept_b} affect the {concept_c} of the system? Justify your answer."
    ],
    "Mathematics": [
        "Using {concept_a}, prove that {concept_b}. Hence, find the value of {concept_c}.",
        "Evaluate the {concept_a} of the function {concept_b}. State the conditions under which this is valid.",
        "Solve the following {concept_a}: {concept_b}. Show all essential working steps."
    ],
    "Biology": [
        "Differentiate between {concept_a} and {concept_b} on the basis of {concept_c}.",
        "Describe the process of {concept_a} with the help of a well-labelled diagram. Mention its significance in {concept_b}.",
        "Explain the role of {concept_a} in {concept_b}. What would be the physiological consequence if it is deficient?"
    ],
    "Computer Science": [
        "Define {concept_a}. Write a {concept_b} in Java to demonstrate its implementation, including appropriate comments.",
        "Reduce the following {concept_a} using {concept_b}. Draw the corresponding logic gate diagram.",
        "Differentiate between {concept_a} and {concept_b} with respect to {concept_c}. Provide a real-world example of each."
    ]
}

ANSWER_OUTLINES = {
    "Physics": "1. State the core principle/definition. 2. Provide the step-by-step mathematical derivation. 3. Substitute the modified variables. 4. Conclude with the final relationship and SI units.",
    "Chemistry": "1. State the relevant chemical principle or law. 2. Provide the balanced chemical equation with state symbols. 3. Explain the mechanism or reasoning (e.g., electronic configuration, steric hindrance).",
    "Mathematics": "1. State the theorem or formula being applied. 2. Show step-by-step algebraic manipulation or integration/differentiation. 3. State the final answer with appropriate conditions/domain.",
    "Biology": "1. Provide a clear, concise definition. 2. Describe the process sequentially. 3. Mention the specific biological significance or clinical/physiological consequence.",
    "Computer Science": "1. Provide the formal definition. 2. Write syntactically correct code with variable declarations and comments. 3. State the time/space complexity or draw the requested diagram."
}

def load_and_analyze_data() -> pd.DataFrame:
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Question database not found at {INPUT_CSV}.")
    df = pd.read_csv(INPUT_CSV)
    df = df.fillna({"topic_mapping": "General", "subject": "Unknown", "estimated_marks": 2})
    return df

def extract_concepts(df: pd.DataFrame, subject: str, topic: str) -> List[str]:
    """Extract unique keywords/concepts from the text of questions mapped to a specific topic."""
    subset = df[(df["subject"] == subject) & (df["topic_mapping"] == topic)]
    if subset.empty:
        return ["core principles", "fundamental laws", "standard applications"]
    
    # Simple keyword extraction: take the most frequent meaningful words (length > 4)
    text = " ".join(subset["question_text"].astype(str).tolist()).lower()
    words = [w.strip(".,()[]{}\"'") for w in text.split() if len(w) > 4 and w.isalpha()]
    
    # Get unique concepts, prioritizing those that appear multiple times
    from collections import Counter
    common_words = [word for word, count in Counter(words).most_common(15)]
    
    # Fallback if extraction yields too few words
    if len(common_words) < 3:
        common_words.extend(["phenomenon", "principle", "calculation", "evaluation"])
        
    return list(set(common_words))[:5] # Return up to 5 unique concepts

def generate_practice_questions(df: pd.DataFrame) -> List[PracticeQuestion]:
    practice_set = []
    subjects = df["subject"].unique()
    q_id_counter = 1
    
    for subject in subjects:
        if subject == "Unknown":
            continue
            
        topics = df[df["subject"] == subject]["topic_mapping"].unique()
        subject_templates = TEMPLATES.get(subject, TEMPLATES["Physics"])
        answer_template = ANSWER_OUTLINES.get(subject, ANSWER_OUTLINES["Physics"])
        
        # Select up to 3 topics per subject to ensure broad coverage (including low-frequency)
        selected_topics = random.sample(list(topics), min(3, len(topics)))
        
        for topic in selected_topics:
            concepts = extract_concepts(df, subject, topic)
            if len(concepts) < 3:
                concepts.extend(["concept A", "concept B", "concept C"])
                
            # Synthesize a question using a random template and extracted concepts
            template = random.choice(subject_templates)
            try:
                synthesized_q = template.format(
                    concept_a=concepts[0].capitalize(),
                    concept_b=concepts[1].capitalize(),
                    concept_c=concepts[2].capitalize()
                )
            except KeyError:
                synthesized_q = f"Explain the relationship between {concepts[0]} and {concepts[1]} in the context of {topic}."
            
            # Determine difficulty based on estimated marks from source data
            avg_marks = df[(df["subject"] == subject) & (df["topic_mapping"] == topic)]["estimated_marks"].mean()
            difficulty = "hard" if avg_marks >= 4 else ("medium" if avg_marks >= 2 else "easy")
            
            pq = PracticeQuestion(
                practice_question_id=f"PQ_{subject.replace(' ', '')}_{q_id_counter:03d}",
                question=synthesized_q,
                subject=subject,
                chapter="Syllabus Aligned", # Can be refined with a full syllabus map
                topic=topic,
                question_type="structured_long_answer" if avg_marks >= 4 else "short_answer",
                marks=int(avg_marks) if avg_marks > 0 else 2,
                difficulty=difficulty,
                source_basis=[f"ISC {subject} {year}" for year in df[(df["subject"]==subject) & (df["topic_mapping"]==topic)]["source_year"].unique()[:3]],
                reason_for_inclusion=f"Ensures coverage of '{topic}', a core syllabus area observed in historical papers.",
                not_a_prediction=True,
                answer_outline=answer_template,
                verification_notes=["Verify specific numerical values if applicable.", "Ensure diagram requirements match latest CISCE guidelines."]
            )
            practice_set.append(pq)
            q_id_counter += 1
            
    return practice_set

def main():
    logging.info("Starting Stage K: Practice Question Generation...")
    
    try:
        df = load_and_analyze_data()
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return
        
    logging.info(f"Analyzing {len(df)} extracted questions to synthesize practice material...")
    practice_set = generate_practice_questions(df)
    
    # Export to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump([asdict(pq) for pq in practice_set], f, indent=2)
        
    # Export to CSV
    if practice_set:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(practice_set[0]).keys())
            writer.writeheader()
            for pq in practice_set:
                writer.writerow(asdict(pq))
                
    logging.info(f"✅ Successfully generated {len(practice_set)} original practice questions.")
    logging.info(f"Saved to: {OUTPUT_JSON} and {OUTPUT_CSV}")

if __name__ == "__main__":
    main()