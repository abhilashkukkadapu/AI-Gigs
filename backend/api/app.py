from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from pydantic import BaseModel

from backend.videoai.core.storage import HLS_DIR, ORIGINALS_DIR, EXPORTS_DIR, create_asset_record, list_assets, load_asset, save_asset
from backend.worker.jobs import process_asset

try:
    from rq import Queue
    from redis import Redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(REDIS_URL)
    queue = Queue("video", connection=redis_conn)
except Exception:
    redis_conn = None
    queue = None
    logger.warning("Redis not available; jobs will run inline")

app = FastAPI(title="Video AI + Media Management API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    renditions: Optional[List[dict]] = None


@app.get("/assets")
async def get_assets():
    return [a.to_dict() for a in list_assets()]


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    filename = file.filename
    dest = ORIGINALS_DIR / filename
    # Avoid overwriting existing files with same name
    i = 1
    while dest.exists():
        dest = ORIGINALS_DIR / f"{dest.stem}_{i}{dest.suffix}"
        i += 1

    async with aiofiles.open(dest, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await f.write(chunk)

    asset = create_asset_record(dest.name, dest)
    logger.info("Uploaded asset {} -> {}", asset.id, dest)
    return asset.to_dict()


@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    asset = load_asset(asset_id)
    if not asset:
        return JSONResponse({"error": "not found"}, status_code=404)
    return asset.to_dict()

@app.post("/process/{asset_id}")
async def enqueue_process(asset_id: str, req: ProcessRequest | None = None):
    req = req or ProcessRequest()
    if queue:
        job = queue.enqueue(process_asset, asset_id, req.renditions)
        return {"job_id": job.id}
    # Fallback: run inline
    result = process_asset(asset_id, req.renditions)
    return result


@app.get("/stream/{asset_id}/master.m3u8")
async def serve_master(asset_id: str):
    path = HLS_DIR / asset_id / "master.m3u8"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path)


@app.get("/stream/{asset_id}/{variant}/{segment}")
async def serve_segment(asset_id: str, variant: str, segment: str):
    path = HLS_DIR / asset_id / variant / segment
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path)


@app.get("/exports/{asset_id}/{kind}")
async def serve_export(asset_id: str, kind: str):
    path = EXPORTS_DIR / asset_id / f"{asset_id}.{kind}"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path)
