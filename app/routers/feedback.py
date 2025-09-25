from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form
from app import database, models
from app.api.groq_client import analyze_resume_with_groq
from app.core.logger import get_logger
from app.utils.pdf_utils import extract_keywords, extract_resume_text
from app.utils.utils import get_current_user
import io
import re


router = APIRouter(prefix="/ai", tags=["Feedback"])

logger = get_logger(__name__)

MAX_FILE_SIZE_MB = 2
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024 


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/resume/extract")
async def extract_resume(
    resume: UploadFile,
    current_user: models.User = Depends(get_current_user),

    ):
    file_bytes = await resume.read()

    if not file_bytes:
        logger.warning("Uploaded file is empty")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    extracted_text = extract_resume_text(file_bytes, resume.content_type, resume.filename)

    if not extracted_text:
        logger.error(f"Failed to extract text from: {resume.filename}")
        raise HTTPException(status_code=422, detail="Could not extract text from file.")

    logger.info(f"Successfully extracted resume: {resume.filename}")

    return {
        "success": True,
        "filename": resume.filename,
        "word_count": len(extracted_text.split()),
        "extracted_text_preview": extracted_text[:500]
    }

# app/routes/resume.py




@router.post("/resume/analyze")
async def analyze_resume(
    resume: UploadFile,
    job_description: str = Form(...),
    current_user: models.User = Depends(get_current_user),

    ):
    """
    Analyze a resume against a job description using Groq AI.
    """
    try:
        # ✅ Read file
        file_bytes = await resume.read()
        if not file_bytes:
            logger.warning("Uploaded file is empty")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
            )

        # ✅ Extract text
        resume_text = extract_resume_text(
            file_bytes, resume.content_type, resume.filename
        )
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume")

        # ✅ Call Groq AI
        insights = analyze_resume_with_groq(resume_text, job_description)

        return {
            "filename": resume.filename,
            "extracted_text_preview": resume_text[:500],  # preview only
            "analysis": insights,
        }

    except Exception as e:
        logger.exception("Resume analysis failed")
        raise HTTPException(status_code=500, detail=str(e))



