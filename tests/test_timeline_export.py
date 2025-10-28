from backend.videoai.timeline.model import build_timeline_from_scenes
from backend.videoai.timeline.export.edl import export_edl
from backend.videoai.timeline.export.fcpxml import export_fcpxml


def test_edl_and_fcpxml_exports_basic():
    scenes = [0.0, 2.0, 5.5]
    timeline = build_timeline_from_scenes(scenes, duration=10.0, source="video.mp4")
    edl = export_edl(timeline, title="Test")
    fcpxml = export_fcpxml(timeline, title="Test")
    assert "TITLE: Test" in edl
    assert "<fcpxml" in fcpxml
    assert "asset-clip" in fcpxml
