from typing import Dict
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Body
from app import database, models
from app.api.groq_client import analyze_resume_with_groq, clean_resume_json, extract_resume_json_with_groq
from app.core.logger import get_logger
from app.utils.pdf_converter import pdf_to_editable_html, pdf_to_html_preview
from app.utils.pdf_overlay_extractor import extract_pdf_structure
from app.utils.pdf_utils import extract_resume_text
from app.utils.utils import get_current_user


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
    # current_user: models.User = Depends(get_current_user),

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
        
        # try:
        #     resume_json = extract_resume_json_with_groq(resume_text)  # <-- you need to build this fn
        # except Exception as e:
        #     logger.exception("Resume JSON extraction failed")
        #     raise HTTPException(status_code=500, detail="Failed to parse resume into structured data")
        
        # # ✅ Convert JSON back to clean text
        # resume_text_for_ai = resume_to_text(resume_json)
    

        # ✅ Call Groq AI
        try:
            insights = analyze_resume_with_groq(resume_text, job_description)
            
        except Exception as e:
            logger.exception("Groq AI analysis failed")
            raise HTTPException(status_code=500, detail="AI analysis failed")    

        return {
            "filename": resume.filename,
            "extracted_text_preview": resume_text[:500],  # preview only
            "analysis": insights,
            # "resume_json": resume_json
        }

    except Exception as e:
        logger.exception("Resume analysis failed")
        raise HTTPException(status_code=500, detail=str(e))



    
@router.post("/extract-pdf-structure")
async def extract_pdf(file: UploadFile = File(...)):
    file_bytes = await file.read()
    return extract_pdf_structure(file_bytes)    



@router.post("/resume/reanalyze")
async def reanalyze_resume(
    resume: str = Form(...),
    job_description: str = Form(...),
):
    if not resume:
        raise HTTPException(status_code=400, detail="Missing resume data")

        
    try:
        insights = analyze_resume_with_groq(resume, job_description)
    except Exception as e:
        logger.exception("Groq AI re-analysis failed")
        raise HTTPException(status_code=500, detail="AI re-analysis failed")    

    

    return {
        "analysis": insights,
        
        }
    
    
    
@router.post("/resume/structure")
async def structure_resume(
    resume: UploadFile,
    # current_user: models.User = Depends(get_current_user),
):
    """
    Convert a resume into structured JSON (ResumeData).
    Only called when user wants to edit.
    """
    try:
        file_bytes = await resume.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large.")

        # Step 1: Extract raw text
        resume_text = extract_resume_text(file_bytes, resume.content_type, resume.filename)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume")

        # Step 2: Call Groq extractor
        resume_json = extract_resume_json_with_groq(resume_text)

        # Step 3: Normalize dates (YYYY-MM format)
        resume_json = clean_resume_json(resume_json)

        return {
            "filename": resume.filename,
            "resume_json": resume_json,
        }
        
   

    except Exception as e:
        logger.exception("Resume structuring failed")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
def resume_to_text(resume: dict) -> str:
    """Convert ResumeData dict to plain text string for AI analysis."""
    lines = []
    personal = resume.get("personalInfo", {})
    lines.append(personal.get("fullName", ""))
    lines.append(personal.get("title", ""))
    lines.append(personal.get("email", ""))
    lines.append(personal.get("phone", ""))
    lines.append(personal.get("location", ""))
    lines.append(personal.get("linkedin", ""))
    lines.append(personal.get("website", ""))
    
    if resume.get("summary"):
        lines.append("\n=== SUMMARY ===\n" + resume["summary"])

    # Experience (sorted descending by startDate if possible)
    experiences = resume.get("experience", [])
    experiences = sorted(
        experiences, key=lambda x: x.get("startDate", ""), reverse=True
    )
    if experiences:
        lines.append("\n=== EXPERIENCE ===")
        for exp in experiences:
            lines.append(f"{exp.get('role','')} at {exp.get('company','')} ({exp.get('startDate','')} - {exp.get('endDate','Present')})")
            for ach in exp.get("achievements", []):
                lines.append(f" - {ach}")

    # Education
    education = resume.get("education", [])
    if education:
        lines.append("\n=== EDUCATION ===")
        for edu in education:
            lines.append(
                f"{edu.get('degree','')} in {edu.get('field','')} at {edu.get('institution','')} ({edu.get('startDate','')} - {edu.get('endDate','')})"
            )

    # Skills
    if resume.get("skills"):
        lines.append("\n=== SKILLS ===\n" + ", ".join(resume["skills"]))

    # Extras
    extras = resume.get("extras", {})
    if extras.get("certifications"):
        lines.append("\n=== CERTIFICATIONS ===\n" + ", ".join(extras["certifications"]))
    if extras.get("languages"):
        lines.append("\n=== LANGUAGES ===\n" + ", ".join(extras["languages"]))

    return "\n".join([line for line in lines if line])
