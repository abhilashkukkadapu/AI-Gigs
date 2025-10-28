from __future__ import annotations

from xml.sax.saxutils import escape

from backend.videoai.timeline.model import Timeline


def export_fcpxml(timeline: Timeline, title: str = "Sequence") -> str:
    # Minimal FCPXML 1.8-like structure
    def tc(seconds: float) -> str:
        return f"{seconds}s"

    clips_xml = []
    pos = 0.0
    for track in timeline.tracks:
        for clip in track.clips:
            dur = clip.end - clip.start
            clips_xml.append(
                f'<asset-clip name="{escape(title)}" start="{tc(clip.start)}" offset="{tc(pos)}" duration="{tc(dur)}" ref="r1"/>'
            )
            pos += dur

    xml = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.8">
  <resources>
    <format id="r2" name="FFVideoFormat1080p24" frameDuration="1/24s" width="1920" height="1080"/>
    <asset id="r1" name="{escape(title)}" start="0s" duration="{tc(timeline.duration)}" hasVideo="1" hasAudio="1" format="r2"/>
  </resources>
  <library>
    <event name="AI Edits">
      <project name="{escape(title)}">
        <sequence duration="{tc(timeline.duration)}" format="r2">
          <spine>
            {''.join(clips_xml)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
""".strip()
    return xml + "\n"
