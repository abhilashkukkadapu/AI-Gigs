from __future__ import annotations

from typing import List

from backend.videoai.timeline.model import Timeline


def _tc(seconds: float) -> str:
    # Format seconds to HH:MM:SS:FF at 24 fps
    fps = 24
    total_frames = int(round(seconds * fps))
    hh = total_frames // (fps * 3600)
    mm = (total_frames % (fps * 3600)) // (fps * 60)
    ss = (total_frames % (fps * 60)) // fps
    ff = total_frames % fps
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def export_edl(timeline: Timeline, title: str = "SEQUENCE") -> str:
    lines: List[str] = [f"TITLE: {title}", "FCM: NON-DROP FRAME"]
    event = 1
    for track_idx, track in enumerate(timeline.tracks, start=1):
        pos = 0.0
        for clip in track.clips:
            src_in = _tc(clip.start)
            src_out = _tc(clip.end)
            rec_in = _tc(pos)
            rec_out = _tc(pos + (clip.end - clip.start))
            lines.append(f"{event:003d}  AX       V     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP: {clip.source}")
            event += 1
            pos += (clip.end - clip.start)
    return "\n".join(lines) + "\n"
