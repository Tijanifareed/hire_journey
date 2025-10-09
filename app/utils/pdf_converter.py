import subprocess
import tempfile
import os
import fitz 
import base64
import html
import statistics
import re




PDF2HTMLEX_PATH =  r"c:\ProgramData\pdf2htmlEX\pdf2htmlEX.exe"
def pdf_to_html_preview(file_bytes: bytes) -> str:
    import tempfile, os, subprocess

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(file_bytes)
        tmp_pdf_path = tmp_pdf.name

    tmp_dir = os.path.dirname(tmp_pdf_path)
    tmp_html_name = os.path.splitext(os.path.basename(tmp_pdf_path))[0] + ".html"
    tmp_html_path = os.path.join(tmp_dir, tmp_html_name)

    try:
        result = subprocess.run(
            [
                PDF2HTMLEX_PATH,
                "--embed", "cfijo",
                "--dest-dir", tmp_dir,
                tmp_pdf_path,
                tmp_html_name,  # only filename, not full path
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"pdf2htmlEX failed (code {result.returncode}):\n"
                f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        with open(tmp_html_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    finally:
        # Always clean up, even if it fails
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
        if os.path.exists(tmp_html_path):
            os.remove(tmp_html_path)

import base64

# def pdf_to_editable_html(file_bytes: bytes) -> str:
#     """Convert PDF to editable HTML (text + images) for TipTap."""
#     doc = fitz.open(stream=file_bytes, filetype="pdf")
#     html_pages = []

#     for page_num, page in enumerate(doc, start=1):
#         # Extract text as HTML
#         page_dict = page.get_text("dict")
#         lines_html = []
#         for block in page_dict.get("blocks", []):
#             if block["type"] == 0:  # text
#                 for line in block["lines"]:
#                     spans_html = []
#                     for span in line["spans"]:
#                         text = span["text"].strip()
#                         if not text:
#                             continue
#                         size = int(round(span["size"]))
#                         font = span["font"].lower()
#                         if "bold" in font:
#                             text = f"<strong>{text}</strong>"
#                         if "italic" in font:
#                             text = f"<em>{text}</em>"
#                         spans_html.append(text)
#                     if spans_html:
#                         lines_html.append(
#                             f'<p style="font-size:{size}px;">{" ".join(spans_html)}</p>'
#                         )
#         text_html = "\n".join(lines_html)


#         # Extract images
#         images_html = []
#         for img_index, img in enumerate(page.get_images(full=True)):
#             xref = img[0]
#             base_image = doc.extract_image(xref)
#             image_bytes = base_image["image"]
#             image_ext = base_image["ext"]

#             # Encode to base64
#             image_b64 = base64.b64encode(image_bytes).decode("utf-8")
#             img_tag = f'<img src="data:image/{image_ext};base64,{image_b64}" alt="pdf-image-{page_num}-{img_index}" />'
#             images_html.append(img_tag)

#         page_content = f"""
#         <div class="pdf-page" data-page="{page_num}">
#             {text_html}
#             {"".join(images_html)}
#         </div>
#         """
#         html_pages.append(page_content)

#     doc.close()

#     return "<div class='pdf-document'>" + "\n".join(html_pages) + "</div>"


# def pdf_to_editable_html(file_bytes: bytes) -> str:
#     """Convert PDF to structured editable HTML (with headings, lists, paragraphs, images)."""
#     import base64
#     doc = fitz.open(stream=file_bytes, filetype="pdf")
#     html_pages = []

#     for page_num, page in enumerate(doc, start=1):
#         page_dict = page.get_text("dict")
#         lines_html = []
#         current_list = []

#         for block in page_dict.get("blocks", []):
#             if block["type"] == 0:  # text
#                 for line in block["lines"]:
#                     spans_html = []
#                     size = None

#                     for span in line["spans"]:
#                         text = span["text"].strip()
#                         if not text:
#                             continue

#                         size = int(round(span["size"]))
#                         font = span["font"].lower()

#                         # Styling
#                         if "bold" in font:
#                             text = f"<strong>{text}</strong>"
#                         if "italic" in font:
#                             text = f"<em>{text}</em>"

#                         spans_html.append(text)

#                     if spans_html:
#                         line_text = " ".join(spans_html)

#                         # Detect bullet points
#                         if line_text.startswith(("•", "-", "●")):
#                             item = line_text.lstrip("•-● ").strip()
#                             current_list.append(f"<li>{item}</li>")
#                         else:
#                             # Flush current list if ended
#                             if current_list:
#                                 lines_html.append("<ul>" + "".join(current_list) + "</ul>")
#                                 current_list = []

#                             # Headings vs body text
#                             if size and size >= 18:
#                                 lines_html.append(f"<h2>{line_text}</h2>")
#                             elif size and size >= 14:
#                                 lines_html.append(f"<h3>{line_text}</h3>")
#                             else:
#                                 lines_html.append(f"<p style='font-size:{size}px'>{line_text}</p>")

#             elif block["type"] == 1:  # image
#                 base_image = doc.extract_image(block["image"])
#                 image_bytes = base_image["image"]
#                 image_ext = base_image["ext"]
#                 image_b64 = base64.b64encode(image_bytes).decode("utf-8")
#                 lines_html.append(
#                     f'<img src="data:image/{image_ext};base64,{image_b64}" alt="pdf-image-{page_num}" />'
#                 )

#         # Flush any remaining list
#         if current_list:
#             lines_html.append("<ul>" + "".join(current_list) + "</ul>")

#         page_content = f"""
#         <div class="pdf-page" data-page="{page_num}">
#             {"".join(lines_html)}
#         </div>
#         """
#         html_pages.append(page_content)

#     doc.close()
#     return "<div class='pdf-document'>" + "\n".join(html_pages) + "</div>"


# app/utils/pdf_converter.py

# Regex for bullets: •, -, *, •, 1. etc
_bullet_re = re.compile(r"^(?:[\u2022\u2023\u25E6\•\-\*\u2013]|\d+\.)\s+")

def _pt_to_px(pt: float) -> int:
    """Convert PDF points to CSS pixels (1pt ≈ 1.333px)."""
    return max(10, int(round(pt * 96.0 / 72.0)))

def _escape(t: str) -> str:
    return html.escape(t).replace("\n", "<br/>")

def pdf_to_editable_html(file_bytes: bytes) -> str:
    """
    Convert PDF to structured HTML (close to original).
    Preserves headings, paragraphs, lists, bold/italic, spacing, and images.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_pages = []

    for page_num, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict")
        spans = []
        sizes = []

        # --- Collect spans ---
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_y = line.get("bbox", [0, 0, 0, 0])[1]
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    font = span.get("font", "").lower()
                    size = span.get("size", 12.0)
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    is_bold = "bold" in font or "black" in font
                    is_italic = "italic" in font or "oblique" in font

                    spans.append({
                        "text": text,
                        "size": size,
                        "font": font,
                        "y": line_y,
                        "x": bbox[0],
                        "bold": is_bold,
                        "italic": is_italic,
                    })
                    sizes.append(size)

        # If no text, maybe images only
        if not spans:
            imgs_html = []
            for img_idx, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                b64 = base64.b64encode(base_image["image"]).decode("utf-8")
                imgs_html.append(
                    f'<img src="data:image/{base_image["ext"]};base64,{b64}" '
                    f'alt="img-{page_num}-{img_idx}" style="max-width:100%;" />'
                )
            all_pages.append(f"<div class='pdf-page' data-page='{page_num}'>{''.join(imgs_html)}</div>")
            continue

        # --- Stats for font sizes ---
        median_size = statistics.median(sizes) if sizes else 12.0
        spans_sorted = sorted(spans, key=lambda s: (s["y"], s["x"]))

        # --- Group into lines ---
        lines = []
        current_line = {"y": None, "spans": []}
        for s in spans_sorted:
            if current_line["y"] is None:
                current_line = {"y": s["y"], "spans": [s]}
                lines.append(current_line)
            else:
                if abs(s["y"] - current_line["y"]) <= (median_size * 0.6):
                    current_line["spans"].append(s)
                else:
                    current_line = {"y": s["y"], "spans": [s]}
                    lines.append(current_line)

        # --- Group into paragraphs ---
        paragraphs = []
        cur_para = {"lines": [], "max_size": 0}
        prev_y = None
        for ln in lines:
            span_htmls = []
            line_max_size = 0
            for s in ln["spans"]:
                t = _escape(s["text"])
                if s["bold"]: t = f"<strong>{t}</strong>"
                if s["italic"]: t = f"<em>{t}</em>"
                span_htmls.append(t)
                line_max_size = max(line_max_size, s["size"])

            line_html = " ".join(span_htmls).strip()
            plain_text = "".join([sp["text"] for sp in ln["spans"]]).strip()
            is_bullet = bool(_bullet_re.match(plain_text))

            if prev_y is None:
                cur_para["lines"].append({"html": line_html, "is_bullet": is_bullet, "plain": plain_text})
                cur_para["max_size"] = max(cur_para["max_size"], line_max_size)
            else:
                gap = ln["y"] - prev_y
                if gap > (median_size * 1.2):  # new paragraph
                    paragraphs.append(cur_para)
                    cur_para = {"lines": [{"html": line_html, "is_bullet": is_bullet, "plain": plain_text}], "max_size": line_max_size}
                else:
                    cur_para["lines"].append({"html": line_html, "is_bullet": is_bullet, "plain": plain_text})
                    cur_para["max_size"] = max(cur_para["max_size"], line_max_size)

            prev_y = ln["y"]

        if cur_para["lines"]:
            paragraphs.append(cur_para)

        # --- Render paragraphs ---
        page_parts = []
        for para in paragraphs:
            max_sz = para["max_size"] or median_size
            text_length = sum(len(l["plain"]) for l in para["lines"])
            is_heading = (max_sz >= median_size * 1.25) and (text_length < 200)

            if all(l["is_bullet"] for l in para["lines"]):
                lis = [f"<li>{_bullet_re.sub('', l['html']).strip()}</li>" for l in para["lines"]]
                page_parts.append("<ul>" + "".join(lis) + "</ul>")
            elif is_heading:
                px = _pt_to_px(max_sz)
                heading_text = " ".join(l["html"] for l in para["lines"])
                page_parts.append(f'<h2 style="font-size:{px}px;margin:4px 0;">{heading_text}</h2>')
            else:
                para_html = " ".join(l["html"] for l in para["lines"])
                px = _pt_to_px(max_sz)
                page_parts.append(f'<p style="font-size:{px}px;margin:4px 0;">{para_html}</p>')

        # --- Images ---
        imgs_html = []
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            b64 = base64.b64encode(base_image["image"]).decode("utf-8")
            imgs_html.append(
                f'<img src="data:image/{base_image["ext"]};base64,{b64}" '
                f'alt="pdf-image-{page_num}-{img_idx}" style="max-width:100%;margin:8px 0;" />'
            )

        all_pages.append(f"<div class='pdf-page' data-page='{page_num}'>{''.join(page_parts)}{''.join(imgs_html)}</div>")

    doc.close()
    return "<div class='pdf-document'>" + "\n".join(all_pages) + "</div>"
