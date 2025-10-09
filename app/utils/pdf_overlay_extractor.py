import fitz  # PyMuPDF
from typing import Dict, Any, List

def extract_pdf_structure(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts structured PDF text + layout for overlay editing.
    Returns JSON with page size and positioned text spans.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []

    for page_num, page in enumerate(doc, start=1):
        page_width, page_height = page.rect.width, page.rect.height
        page_dict = page.get_text("dict")

        items: List[Dict[str, Any]] = []

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue  # only text blocks
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    x0, y0, x1, y1 = span.get("bbox", [0, 0, 0, 0])
                    items.append({
                        "text": text,
                        "x": x0,
                        "y": y0,
                        "width": x1 - x0,
                        "height": y1 - y0,
                        "fontSize": span.get("size", 12),
                        "fontFamily": span.get("font", "Helvetica"),
                        "color": span.get("color", 0),
                        "page": page_num
                    })

        pages.append({
            "page": page_num,
            "width": page_width,
            "height": page_height,
            "items": items
        })

    doc.close()

    return {"pages": pages}
