"""
Quick local test: reads a transcript from stdin (or a file),
runs extraction + doc generation, and opens the output file.
Usage:
    python test_local.py                   # paste transcript interactively
    python test_local.py transcript.txt    # read from file
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

from extractor import extract_fields, generate_summary
from doc_generator import generate_doc

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            transcript = f.read()
    else:
        print("הדבק את התמלול ולחץ Ctrl+D (Linux/Mac) או Ctrl+Z ואנטר (Windows):")
        transcript = sys.stdin.read()

    print("\n⏳ מחלץ שדות באמצעות GPT...")
    fields = extract_fields(transcript)

    print("✅ שדות שחולצו:")
    for k, v in fields.items():
        if v:
            print(f"  {k}: {v}")

    print("\n� מייצר סיכום מבצעי...")
    summary = generate_summary(transcript)
    print("✅ סיכום:")
    for k, v in summary.items():
        if v:
            print(f"  {k}: {v}")

    print("\n📄 מייצר מסמך Word...")
    path = generate_doc(fields, transcript, summary=summary)
    print(f"✅ המסמך נשמר: {path}")

    # Try to open automatically
    if sys.platform == "win32":
        os.startfile(path)

if __name__ == "__main__":
    main()
