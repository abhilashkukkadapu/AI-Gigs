from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# Base directories can be customized via environment variables
BASE_DIR = Path(os.environ.get("PROJECT_ROOT", "/workspace"))
MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", str(BASE_DIR / "media")))
ORIGINALS_DIR = Path(os.environ.get("ORIGINALS_DIR", str(MEDIA_DIR / "originals")))
HLS_DIR = Path(os.environ.get("HLS_DIR", str(MEDIA_DIR / "hls")))
EXPORTS_DIR = Path(os.environ.get("EXPORTS_DIR", str(BASE_DIR / "exports")))
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
ASSETS_DIR = DATA_DIR / "assets"

for d in [MEDIA_DIR, ORIGINALS_DIR, HLS_DIR, EXPORTS_DIR, DATA_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class Asset:
    id: str
    filename: str
    original_path: str
    uploaded_at: str
    status: str = "uploaded"  # uploaded | processing | ready | failed
    hls_path: Optional[str] = None
    scene_cuts: Optional[List[float]] = None
    faces: Optional[List[Dict[str, Any]]] = None
    timeline: Optional[Dict[str, Any]] = None
    exports: Optional[Dict[str, str]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def asset_json_path(asset_id: str) -> Path:
    return ASSETS_DIR / f"{asset_id}.json"


def save_asset(asset: Asset) -> None:
    path = asset_json_path(asset.id)
    path.write_text(json.dumps(asset.to_dict(), indent=2))
    logger.info("Saved asset {} -> {}", asset.id, path)


def load_asset(asset_id: str) -> Optional[Asset]:
    path = asset_json_path(asset_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Asset(**data)


def list_assets() -> List[Asset]:
    items: List[Asset] = []
    for p in ASSETS_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text())
            items.append(Asset(**data))
        except Exception as exc:
            logger.warning("Failed to read {}: {}", p, exc)
    # Newest first
    items.sort(key=lambda a: a.uploaded_at, reverse=True)
    return items


def create_asset_record(filename: str, original_path: Path) -> Asset:
    asset_id = uuid.uuid4().hex
    record = Asset(
        id=asset_id,
        filename=filename,
        original_path=str(original_path),
        uploaded_at=datetime.utcnow().isoformat() + "Z",
        status="uploaded",
    )
    save_asset(record)
    return record
