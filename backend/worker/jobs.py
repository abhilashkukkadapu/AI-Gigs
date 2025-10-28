from __future__ import annotations

import traceback
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from backend.videoai.core.ffmpeg import DEFAULT_RENDITIONS, Rendition, probe_video, transcode_to_hls
from backend.videoai.core.storage import EXPORTS_DIR, HLS_DIR, load_asset, save_asset
from backend.videoai.ai.scene_detection import detect_scenes
from backend.videoai.ai.face_detection import detect_faces_samples
from backend.videoai.timeline.model import Timeline, build_timeline_from_scenes
from backend.videoai.timeline.export.edl import export_edl
from backend.videoai.timeline.export.fcpxml import export_fcpxml


def process_asset(asset_id: str, renditions: Optional[List[Dict]] = None) -> Dict:
    logger.info("Processing asset {}", asset_id)
    asset = load_asset(asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    asset.status = "processing"
    save_asset(asset)

    try:
        input_path = Path(asset.original_path)
        # 1) Transcode to HLS
        r_objs = DEFAULT_RENDITIONS if not renditions else [
            Rendition(**r) for r in renditions
        ]
        asset_hls_dir = HLS_DIR / asset.id
        master_m3u8 = transcode_to_hls(input_path, asset_hls_dir, r_objs)
        asset.hls_path = str(master_m3u8)

        # 2) AI: scene detection
        scenes = detect_scenes(input_path)
        asset.scene_cuts = scenes

        # 3) Face detection (sampled)
        faces = detect_faces_samples(input_path)
        asset.faces = faces

        # 4) Build timeline from scenes
        probe = probe_video(input_path)
        duration = float(probe["format"]["duration"]) if probe.get("format", {}).get("duration") else 0.0
        timeline: Timeline = build_timeline_from_scenes(scenes, duration, str(input_path))
        asset.timeline = timeline.model_dump()

        # 5) Exports
        edl_text = export_edl(timeline, title=asset.filename)
        fcpxml_text = export_fcpxml(timeline, title=asset.filename)

        exports_dir = EXPORTS_DIR / asset.id
        exports_dir.mkdir(parents=True, exist_ok=True)
        edl_path = exports_dir / f"{asset.id}.edl"
        fcpxml_path = exports_dir / f"{asset.id}.fcpxml"
        edl_path.write_text(edl_text)
        fcpxml_path.write_text(fcpxml_text)

        asset.exports = {"edl": str(edl_path), "fcpxml": str(fcpxml_path)}

        asset.status = "ready"
        save_asset(asset)
        logger.info("Completed processing asset {}", asset.id)
        return {"status": asset.status, "asset_id": asset.id}
    except Exception as exc:
        logger.error("Processing failed for {}: {}\n{}", asset.id, exc, traceback.format_exc())
        asset.status = "failed"
        asset.error = str(exc)
        save_asset(asset)
        return {"status": asset.status, "asset_id": asset.id, "error": str(exc)}
