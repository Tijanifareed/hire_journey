import time, hashlib
from fastapi import APIRouter, Depends
from app.utils.utils import get_current_user
import cloudinary

router = APIRouter(prefix="/cloudinary", tags=["Cloudinary"])

@router.get("/signature")
def get_upload_signature(current_user=Depends(get_current_user)):
    timestamp = int(time.time())
    params = {
        "timestamp": timestamp,
        "folder": "user_profiles",
    }

    # generate signature
    api_secret = cloudinary.config().api_secret
    signature = hashlib.sha1(
        "&".join([f"{k}={v}" for k, v in sorted(params.items())]).encode("utf-8") 
        + api_secret.encode("utf-8")
    ).hexdigest()

    return {
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": cloudinary.config().cloud_name,
        "api_key": cloudinary.config().api_key,
        "folder": "user_profiles",
    }
