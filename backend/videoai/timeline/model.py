from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Clip(BaseModel):
    source: str
    start: float
    end: float


class Track(BaseModel):
    clips: List[Clip] = Field(default_factory=list)


class Timeline(BaseModel):
    tracks: List[Track] = Field(default_factory=list)
    duration: float


def build_timeline_from_scenes(scene_starts: List[float], duration: float, source: str) -> Timeline:
    # Convert scene starts to clip ranges [start, end)
    if not scene_starts:
        scene_starts = [0.0]
    # Ensure sorted and unique
    starts = sorted(set(scene_starts))
    ends: List[float] = starts[1:] + [duration]
    clips = [Clip(source=source, start=float(s), end=float(e)) for s, e in zip(starts, ends) if e > s]
    return Timeline(tracks=[Track(clips=clips)], duration=float(duration))
