import os
from app import database
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from app import models, database
from app.schema.schemas import AddResumeRequest
from app.utils.utils import get_current_user
import cloudinary.uploader
from typing import Dict
from fastapi.responses import StreamingResponse
import io
import requests


router = APIRouter(prefix="/resume", tags=["Resume"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/add/resume")
def upload_resume(
    resume_data: AddResumeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing_resumes = db.query(models.Resume).filter(models.Resume.user_id == current_user.id).count()

    if existing_resumes >= 5:
        try:
            cloudinary.uploader.destroy(resume_data.public_id)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to cleanup Cloudinary file: {str(e)}"
            )
        
        raise HTTPException(
            status_code=400,
            detail="You can only upload a maximum of 3 resumes."
        )

    # Create new resume entry
    new_resume = models.Resume(
        name=resume_data.title,
        file_url=resume_data.file_url,
        public_id=resume_data.public_id,
        user_id=current_user.id
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return {
        "message": "Resume uploaded successfully.",
        "resume": {
            "id": new_resume.id,
            "name": new_resume.name,
            "file_url": new_resume.file_url
        }
    }


@router.delete("/delete-resume/{resume_id}")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a resume (and also remove it from Cloudinary).
    """
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete from Cloudinary
    try:
        cloudinary.uploader.destroy(resume.public_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary delete failed: {str(e)}")

    # Delete from DB
    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted successfully"}


@router.get("/my-resumes")
def list_resumes(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    resumes = db.query(models.Resume).filter(models.Resume.user_id == current_user.id).all()
    if not resumes:
        return {"message": "You have no resume."}
    return {"resumes": resumes}

@router.get("/my-resumes/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id
    ).first()
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"resume": resume}


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> Dict:
    try:
        # TODO: parse PDF -> ResumeData (mock for now)
        resume = {
            "personalInfo": {
                "fullName": "John Doe",
                "email": "john@example.com",
            },
            "summary": "Results-driven software engineer...",
            "experience": [],
            "education": [],
            "skills": []
        }
        # TODO: run initial analysis (mock numbers)
        analysis = {
            "atsScore": 65,
            "keywordMatch": 70,
            "missingKeywords": ["Python", "Docker"],
            "suggestions": ["Add measurable achievements."]
        }
        return {"resume": resume, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing failed: {e}")
    
    
    import requests
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import io


BROWSERLESS_TOKEN = os.getenv(
    "BROWSERLESS_TOKEN",
    "2TCJXP5xQVFwTO605ef2d89bbff63ea3d864a63219c1f8ec8"
)

@router.post("/export")
async def export_resume(data: dict = Body(...)):
    html = data.get("html")
    if not html:
        raise HTTPException(status_code=400, detail="Missing HTML content")

    payload = {
        # ✅ use HTML exactly as received (no rewrapping)
        "html": html,
        "options": {
            "format": "A4",
            "printBackground": True,
            "preferCSSPageSize": True,
            "margin": {"top": "10mm", "bottom": "10mm"},
        },
    }

    url = f"https://production-sfo.browserless.io/pdf?token={BROWSERLESS_TOKEN}"

    try:
        response = requests.post(url, json=payload, timeout=60)
        print("Browserless status:", response.status_code)
        if response.status_code != 200:
            print("Browserless error:", response.text[:500])
            raise HTTPException(status_code=500, detail="Browserless PDF generation failed")
    except Exception as e:
        print("❌ Request error:", e)
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        io.BytesIO(response.content),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="resume.pdf"'},
    )