from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class Rendition:
    name: str
    width: int
    height: int
    video_bitrate: str  # e.g., "5000k"
    audio_bitrate: str  # e.g., "192k"
    maxrate: str        # e.g., "5350k"
    bufsize: str        # e.g., "7500k"


DEFAULT_RENDITIONS: List[Rendition] = [
    Rendition(name="1080p", width=1920, height=1080, video_bitrate="5000k", audio_bitrate="192k", maxrate="5350k", bufsize="7500k"),
    Rendition(name="720p", width=1280, height=720, video_bitrate="2800k", audio_bitrate="160k", maxrate="2996k", bufsize="4200k"),
    Rendition(name="480p", width=854, height=480, video_bitrate="1400k", audio_bitrate="128k", maxrate="1498k", bufsize="2100k"),
]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> None:
    logger.info("Running command: {}", " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        logger.error(proc.stdout)
        raise RuntimeError(f"Command failed with code {proc.returncode}")
    if proc.stdout:
        logger.debug(proc.stdout)


def probe_video(input_path: Path) -> Dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(input_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {proc.stderr}")
    return json.loads(proc.stdout)


def _variant_bandwidth(bitrate_k: str, audio_k: str) -> int:
    def to_int(k: str) -> int:
        return int(k.rstrip("k"))
    # BANDWIDTH is in bits per second; convert kbits to bits
    return (to_int(bitrate_k) + to_int(audio_k)) * 1000


def generate_master_playlist(output_dir: Path, renditions: List[Rendition]) -> Path:
    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for idx, r in enumerate(renditions):
        bandwidth = _variant_bandwidth(r.video_bitrate, r.audio_bitrate)
        lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={r.width}x{r.height}")
        lines.append(f"{r.name}/index.m3u8")
    content = "\n".join(lines) + "\n"
    master_path = output_dir / "master.m3u8"
    master_path.write_text(content)
    return master_path


def transcode_to_hls(input_path: Path, output_dir: Path, renditions: Optional[List[Rendition]] = None, segment_time: int = 4) -> Path:
    renditions = renditions or DEFAULT_RENDITIONS
    _ensure_dir(output_dir)

    # Create a variant playlist for each rendition
    for r in renditions:
        variant_dir = output_dir / r.name
        _ensure_dir(variant_dir)
        # Force original aspect ratio, pad to ensure exact WxH if desired; here, we scale to fit within box
        vf = f"scale=w={r.width}:h={r.height}:force_original_aspect_ratio=decrease"
        hls_cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-i", str(input_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-profile:v", "main",
            "-preset", "veryfast",
            "-b:v", r.video_bitrate,
            "-maxrate", r.maxrate,
            "-bufsize", r.bufsize,
            "-g", "48",
            "-keyint_min", "48",
            "-sc_threshold", "0",
            "-c:a", "aac",
            "-ar", "48000",
            "-b:a", r.audio_bitrate,
            "-ac", "2",
            "-hls_time", str(segment_time),
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(variant_dir / "seg_%06d.ts"),
            str(variant_dir / "index.m3u8"),
        ]
        run_command(hls_cmd)

    # Create master playlist
    return generate_master_playlist(output_dir, renditions)
