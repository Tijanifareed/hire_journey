from fastapi import APIRouter
from app import database
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schemas import AddResumeRequest
from app.utils.utils import get_current_user
import cloudinary.uploader


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
