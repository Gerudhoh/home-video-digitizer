import easyocr
import re
from datetime import datetime

MONTHS = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
DATE_RE = re.compile(rf"({MONTHS})\s*(\d{{1,2}})\s+(\d{{4}})", re.IGNORECASE)

class OCR:
    @staticmethod
    def extract_text(image_name):
        reader = easyocr.Reader(['en'])
        return reader.readtext(image_name)

    @staticmethod
    def extract_date(ocr_results, min_conf=0.4):
        ordered = sorted(ocr_results, key=lambda r: (r[0][0][1], r[0][0][0]))
        text = " ".join(t for _, t, c in ordered if c >= min_conf)

        m = DATE_RE.search(text)
        if not m:
            return None, text

        month, day, year = m.groups()
        try:
            return datetime.strptime(f"{month} {day} {year}", "%b %d %Y").date(), text
        except ValueError:
            return None, text

