# app/tests/test_resume_extract_load.py
import io
import asyncio
import pytest
from httpx import AsyncClient
from app.main import app

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document


def make_pdf_with_text(text: str) -> bytes:
    """
    Create an in-memory PDF with given text.
    """
    file_stream = io.BytesIO()
    c = canvas.Canvas(file_stream, pagesize=letter)
    c.drawString(100, 750, text)
    c.save()
    return file_stream.getvalue()


def make_docx_with_text(text: str) -> bytes:
    """
    Create an in-memory DOCX with given text.
    """
    file_stream = io.BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(file_stream)
    return file_stream.getvalue()


TOTAL_REQUESTS = 200  # adjust for load


@pytest.mark.asyncio
async def test_resume_extract_high_load():
    async with AsyncClient(app=app, base_url="http://test") as client:
        tasks = []

        for i in range(TOTAL_REQUESTS):
            if i % 2 == 0:  # alternate between PDF and DOCX
                file_bytes = make_pdf_with_text(f"This is resume number {i}")
                files = {"resume": (f"resume_{i}.pdf", io.BytesIO(file_bytes), "application/pdf")}
            else:
                file_bytes = make_docx_with_text(f"Python FastAPI SQL resume {i}")
                files = {"resume": (f"resume_{i}.docx", io.BytesIO(file_bytes),
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

            tasks.append(client.post("/resume/extract", files=files))

        responses = await asyncio.gather(*tasks)

    # check all results
    success_count = sum(1 for r in responses if r.status_code == 200)
    fail_count = TOTAL_REQUESTS - success_count

    print(f"\n✅ {success_count} succeeded, ❌ {fail_count} failed")

    assert success_count >= TOTAL_REQUESTS * 0.95  # allow up to 5% failures under heavy load
