# app/api/routes/jd_proxy.py
import os
from typing import List, Union
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app import models
from app.utils.utils import get_current_user
import httpx

router = APIRouter(prefix="/get-jd-from", tags=["Job Description"])

WORKER_URL = os.getenv("WORKER_URL")


@router.post("/image")
async def get_jd_from_image(
    files: Union[UploadFile, List[UploadFile]] = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """
    Proxy endpoint:
    Accept one or multiple files as 'files',
    forward them to the worker's /jd-image endpoint,
    and return the worker's response.
    """
    try:
        # Normalize to list
        if isinstance(files, UploadFile):
            files = [files]

        forward_files = []
        for f in files:
            content = await f.read()
            forward_files.append(
                (
                    "files",  # match worker param name
                    (f.filename, content, f.content_type or "application/octet-stream"),
                )
            )

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{WORKER_URL}/extract/jd-image",
                files=forward_files,
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Worker error: {resp.text}")

        return resp.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/url")
async def get_jd_from_url(
    payload: dict,
    current_user: models.User = Depends(get_current_user),
):
    """
    Proxy endpoint: Accept a JSON body { "url": "<doc/pdf link>" },
    forward it to the worker service, and return the extracted text.
    """
    try:
        if "url" not in payload:
            raise HTTPException(status_code=400, detail="Missing 'url' in request body")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{WORKER_URL}/extract-text", json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Worker error: {response.text}",
            )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))