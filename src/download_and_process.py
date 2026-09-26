import os
import time
import json
import csv
import hashlib
import logging
import requests
import concurrent.futures
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

import pymupdf as fitz
from pdf2image import convert_from_path
import pytesseract

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")
BIN_DIR = os.path.join(BASE_DIR, "bin")
POPPLER_PATH = os.path.join(BIN_DIR, "poppler", "bin")
TESSERACT_CMD = os.path.join(BIN_DIR, "tesseract", "tesseract.exe")

for d in [DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "pipeline.log")),
        logging.StreamHandler()
    ]
)

@dataclass
class DocumentRecord:
    document_id: str
    title: str
    subject: str
    year: int
    document_type: str
    source_url: str
    local_filename: str
    file_size_bytes: int
    sha256: str
    download_status: str
    extraction_method: str
    page_count: int
    text_length: int
    warnings: List[str]

def get_browser_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def download_file(url: str, filepath: str) -> Dict[str, Any]:
    try:
        response = requests.get(url, headers=get_browser_headers(), timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        if not response.content.startswith(b'%PDF'):
            return {"status": "failed", "error": "Not a valid PDF (HTML block)."}
            
        with open(filepath, "wb") as f:
            f.write(response.content)
            
        return {"status": "success", "size": os.path.getsize(filepath)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_text(filepath: str) -> Dict[str, Any]:
    try:
        doc = fitz.open(filepath)
        text_content = []
        has_native_text = False
        
        for page in doc:
            page_text = page.get_text().strip()
            if page_text:
                has_native_text = True
                text_content.append(page_text)
        
        page_count = len(doc)
        doc.close()
        
        if has_native_text:
            return {"method": "native_text", "text": "\n\n".join(text_content), "pages": page_count}
        else:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            images = convert_from_path(filepath, dpi=300, poppler_path=POPPLER_PATH)
            ocr_text = []
            for img in images:
                ocr_text.append(pytesseract.image_to_string(img, lang="eng"))
            return {"method": "ocr", "text": "\n\n".join(ocr_text), "pages": page_count}
    except Exception as e:
        return {"method": "failed", "text": "", "pages": 0, "error": str(e)}

def process_document(doc_meta):
    filename = f"ISC_{doc_meta['subject']}_{doc_meta['year']}_{doc_meta['document_type']}.pdf".replace(" ", "_")
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        dl_result = download_file(doc_meta["url"], filepath)
        if dl_result["status"] != "success":
            return DocumentRecord(
                document_id="failed", title=doc_meta["title"], subject=doc_meta["subject"],
                year=doc_meta["year"], document_type=doc_meta["document_type"],
                source_url=doc_meta["url"], local_filename=filename,
                file_size_bytes=0, sha256="", download_status="failed",
                extraction_method="none", page_count=0, text_length=0,
                warnings=[dl_result["error"]]
            )
    else:
        dl_result = {"status": "success", "size": os.path.getsize(filepath)}
        
    ext_result = extract_text(filepath)
    sha256 = calculate_sha256(filepath)
    
    # Save extracted text
    txt_path = os.path.join(DOWNLOAD_DIR, filename.replace(".pdf", ".txt"))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(ext_result["text"])
        
    return DocumentRecord(
        document_id=sha256[:16],
        title=doc_meta["title"],
        subject=doc_meta["subject"],
        year=doc_meta["year"],
        document_type=doc_meta["document_type"],
        source_url=doc_meta["url"],
        local_filename=filename,
        file_size_bytes=dl_result["size"],
        sha256=sha256,
        download_status="success",
        extraction_method=ext_result["method"],
        page_count=ext_result["pages"],
        text_length=len(ext_result["text"]),
        warnings=[ext_result.get("error")] if ext_result.get("error") else []
    )

def main():
    # MASSIVE CATALOG: 5+ Years of PYQs, Question Banks, and Sample Papers for Science Stream
    documents_to_process = [
        # --- PHYSICS ---
        {"title": "Physics PYQ 2024", "subject": "Physics", "year": 2024, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202024/ISC%20Class%2012/ISC-Class-12-Phys.pdf"},
        {"title": "Physics PYQ 2025", "subject": "Physics", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202025/ISC%2012/Physics%202025.pdf"},
        {"title": "Physics PYQ 2022 Sem 2", "subject": "Physics", "year": 2022, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/pyp/cisce/class12/Physics/Physics%20PY%202022%20Sem%202.pdf"},
        {"title": "Physics PYQ 2025 Board", "subject": "Physics", "year": 2025, "document_type": "previous_year_paper", "url": "https://image-static.collegedunia.com/public/image/ISC_Class_12_Physics_Question_Paper_2025_7273c22bbf2e9cecb9324a75cf845fc1.pdf"},
        {"title": "Physics PYQ 2025 ICSEBoard", "subject": "Physics", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.icseboard.org/pdf/class-10/class-12/papers/physics/2025/isc-class-12-physics-p1-861a-2025.pdf"},
        {"title": "Physics Sample Paper Sem 1 2022", "subject": "Physics", "year": 2022, "document_type": "sample_paper", "url": "https://cdn1.byjus.com/wp-content/uploads/2021/09/ISC-Class-12-Sample-Paper-Physics-Semester-1-for-2022-Exam.pdf"},
        {"title": "Physics Specimen 2024", "subject": "Physics", "year": 2024, "document_type": "specimen_paper", "url": "https://static.collegedekho.com/media/django-summernote/2024-03-04/41cc375a-42e6-4ed8-bdbe-e25bec7b159b.pdf"},
        
        # --- MATHEMATICS ---
        {"title": "Maths PYQ 2025 ICSEBoard", "subject": "Mathematics", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.icseboard.org/pdf/class-10/class-12/papers/mathematics/2025/isc-class-12-mathematics-1225-860-2025.pdf"},
        {"title": "Maths PYQ 2025 Oswaal", "subject": "Mathematics", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202025/ISC%2012/Math%202025.pdf"},
        {"title": "Maths PYQ 2024 Oswaal", "subject": "Mathematics", "year": 2024, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202024/ISC%20Class%2012/2-ISC%20Math-12%20Board%20Papers.pdf"},
        {"title": "Maths PYQ 2024 CollegeDekho", "subject": "Mathematics", "year": 2024, "document_type": "previous_year_paper", "url": "https://static.collegedekho.com/media/uploads/2025/03/03/isc-12th-maths-2024.pdf"},
        {"title": "Maths PYQ 2024 SheetDigest", "subject": "Mathematics", "year": 2024, "document_type": "previous_year_paper", "url": "https://sheetdigest.com/wp-content/uploads/2025/10/ISC-Class-12-Mathematics-Question-Paper-2024.pdf"},
        {"title": "Maths Sample Paper Sem 1 2022", "subject": "Mathematics", "year": 2022, "document_type": "sample_paper", "url": "https://cdn1.byjus.com/wp-content/uploads/2021/09/ISC-Class-12-Sample-Paper-Maths-Semester-1-for-2022-Exam.pdf"},
        {"title": "Maths QB Solved 2018", "subject": "Mathematics", "year": 2018, "document_type": "question_bank", "url": "https://cdn1.byjus.com/wp-content/uploads/2020/09/ISC-Class-12-Maths-Question-Paper-Solution-2018.pdf"},
        
        # --- CHEMISTRY ---
        {"title": "Chemistry PYQ 2023 Oswaal", "subject": "Chemistry", "year": 2023, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/pyp/cisce/class12/Chemistry/Chemistry%20FY%202023.pdf"},
        {"title": "Chemistry PYQ 2023 SheetDigest", "subject": "Chemistry", "year": 2023, "document_type": "previous_year_paper", "url": "https://sheetdigest.com/wp-content/uploads/2025/10/ISC-Class-12-Chemistry-Question-Paper-2023.pdf"},
        {"title": "Chemistry Practical 2020 Byjus", "subject": "Chemistry", "year": 2020, "document_type": "previous_year_paper", "url": "https://cdn1.byjus.com/wp-content/uploads/2021/03/ISC-Class-12-Chemistry-Practical-Question-Paper-2020.pdf"},
        {"title": "Chemistry Syllabus & QB 2024-25", "subject": "Chemistry", "year": 2024, "document_type": "question_bank", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Syllabus/ISC%20Class%2012/2024-25/Chemistry_2dec5205-b8a4-411b-8832-42073b2cefa4.pdf"},
        
        # --- BIOLOGY ---
        {"title": "Biology PYQ 2023 Oswaal", "subject": "Biology", "year": 2023, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Papers%20Files/CISCE%20Class%2012/ISE%20BIOLOGY%20Paper-I.pdf"},
        {"title": "Biology PYQ 2025 Oswaal", "subject": "Biology", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202025/ISC%2012/Bio%202025.pdf"},
        {"title": "Biology PYQ 2024 SheetDigest", "subject": "Biology", "year": 2024, "document_type": "previous_year_paper", "url": "https://sheetdigest.com/wp-content/uploads/2025/10/ISC-Class-12-Biology-Question-Paper-2024.pdf"},
        {"title": "Biology PYQ 2025 ICSEBoard", "subject": "Biology", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.icseboard.org/pdf/class-10/class-12/papers/biology/2025/isc-class-12-biology-p1-1225-863a-2025.pdf"},
        {"title": "Biology PYQ 2025 CollegeDunia", "subject": "Biology", "year": 2025, "document_type": "previous_year_paper", "url": "https://image-static.collegedunia.com/public/image/ISC_Class_12_Biology_Question_Paper_2025_6780bd6522bf1e1761df9106d1a54eda.pdf"},
        {"title": "Biology PYQ 2020 Byjus", "subject": "Biology", "year": 2020, "document_type": "previous_year_paper", "url": "https://cdn1.byjus.com/wp-content/uploads/2021/03/ISC-Class-12-Biology-Question-Paper-2020.pdf"},
        {"title": "Biology QB Solved 2016", "subject": "Biology", "year": 2016, "document_type": "question_bank", "url": "https://cdn1.byjus.com/wp-content/uploads/2020/09/ISC-Class-12-Biology-Question-Paper-Solution-2016.pdf"},
        {"title": "Biology PYQ 2017 Byjus", "subject": "Biology", "year": 2017, "document_type": "previous_year_paper", "url": "https://cdn1.byjus.com/wp-content/uploads/2020/09/ISC-Class-12-Biology-Question-Paper-2017.pdf"},
        
        # --- COMPUTER SCIENCE ---
        {"title": "CS PYQ 2023 Oswaal Solved", "subject": "Computer Science", "year": 2023, "document_type": "question_bank", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Papers%20Files/CISCE%20Class%2012/ISC-12%20Computer%20Science%20Solved%20Paper-2023.pdf"},
        {"title": "CS PYQ 2024 Oswaal", "subject": "Computer Science", "year": 2024, "document_type": "previous_year_paper", "url": "https://www.oswaal360.com/pluginfile.php/10939/mod_folder/content/0/Latest%20Board%20Paper%202024/ISC%20Class%2012/ISC%20COMPUTER%20SCIENCE%202024.pdf"},
        {"title": "CS PYQ 2025 ICSEBoard", "subject": "Computer Science", "year": 2025, "document_type": "previous_year_paper", "url": "https://www.icseboard.org/pdf/class-10/class-12/papers/computer-science/2025/isc-class-12-computer-science-p1-1225-868a-ie-2025.pdf"},
        {"title": "CS PYQ 2025 SheetDigest", "subject": "Computer Science", "year": 2025, "document_type": "previous_year_paper", "url": "https://sheetdigest.com/wp-content/uploads/2025/10/ISC-Class-12-Computer-Science-Question-Paper-2025.pdf"},
        {"title": "CS PYQ 2024 SheetDigest", "subject": "Computer Science", "year": 2024, "document_type": "previous_year_paper", "url": "https://sheetdigest.com/wp-content/uploads/2025/10/ISC-Class-12-Computer-Science-Question-Paper-2024.pdf"},
        {"title": "CS Specimen 2024 CollegeDekho", "subject": "Computer Science", "year": 2024, "document_type": "specimen_paper", "url": "https://static.collegedekho.com/media/uploads/2024/09/06/868-computer-science-paper-1-sqp-ak.pdf"},
        {"title": "CS Syllabus 2024", "subject": "Computer Science", "year": 2024, "document_type": "official_syllabus", "url": "https://cdn1.byjus.com/wp-content/uploads/2021/06/ISC-Class-12-Computer-Science-Syllabus.pdf"}
    ]
    
    catalog = []
    
    logging.info(f"Starting batch download and extraction of {len(documents_to_process)} documents...")
    
    # Use ThreadPoolExecutor for concurrent downloads (max 3 workers to avoid IP bans)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(process_document, documents_to_process))
        
    for res in results:
        catalog.append(res)
        if res.download_status == "success":
            logging.info(f"✅ {res.local_filename} | {res.extraction_method} | {res.text_length} chars")
        else:
            logging.warning(f"❌ {res.local_filename} | FAILED: {res.warnings[0] if res.warnings else 'Unknown'}")

    # Export Catalog
    json_path = os.path.join(OUTPUT_DIR, "isc_catalog.json")
    csv_path = os.path.join(OUTPUT_DIR, "isc_catalog.csv")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in catalog], f, indent=2)
        
    if catalog:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=asdict(catalog[0]).keys())
            writer.writeheader()
            for r in catalog:
                writer.writerow(asdict(r))
                
    logging.info(f"Pipeline complete. Catalog saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()