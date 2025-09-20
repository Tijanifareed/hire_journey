from app.config import cloudinary
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import database, models
from app.schemas import ProfileUpdateRequest
from app.utils.utils import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.get("/user-profile")
def my_profile(
     db: Session = Depends(get_db),
     current_user: models.User = Depends(get_current_user)
):
     user = (
          db.query(models.User)
          .filter(
               models.User.id == current_user.id
          )
          .first()
     )
     if not user:
        raise HTTPException(status_code=404, detail="User detail not found")
     
     return {
          "data": user
     }
     
     
@router.post("/profile-picture")
def save_profile_picture(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_url = payload.get("url")
    if not new_url:
        raise HTTPException(status_code=400, detail="Image URL missing")

    # 1. Delete old image if exists
    if current_user.profile_picture:
        try:
            # Example: https://res.cloudinary.com/<cloud>/image/upload/v123/user_profiles/user_5.png
            old_url = current_user.profile_picture
            public_id = old_url.split("/")[-1].split(".")[0]  # user_5
            folder = "user_profiles"
            cloudinary.uploader.destroy(f"{folder}/{public_id}")
        except Exception as e:
            print(f"Failed to delete old image: {e}")

    # 2. Save new URL
    
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
     # update the user
    user.profile_picture = new_url
    db.commit()
    db.refresh(user)
   


    return {"user": user}



@router.patch("/edit-profile") 
def edit_profile(
     profile_data: ProfileUpdateRequest,
     db: Session = Depends(get_db),
     current_user: models.User = Depends(get_current_user)
):
     update_data = profile_data.dict(exclude_unset=True)
     for field, value in update_data.items():
          setattr(current_user, field, value)
     db.commit()
     db.refresh(current_user)   
     
     return{
          "user": current_user
     }  
      


