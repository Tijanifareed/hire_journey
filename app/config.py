# app/config.py
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader


load_dotenv()  # loads .env file

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)
