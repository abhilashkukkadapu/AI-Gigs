from pathlib import Path

from backend.videoai.core.ffmpeg import _variant_bandwidth, generate_master_playlist, Rendition


def test_variant_bandwidth_and_master_playlist(tmp_path: Path):
    bw = _variant_bandwidth("5000k", "192k")
    assert bw == (5000 + 192) * 1000

    out = tmp_path / "hls"
    out.mkdir()
    master = generate_master_playlist(out, [
        Rendition(name="1080p", width=1920, height=1080, video_bitrate="5000k", audio_bitrate="192k", maxrate="5350k", bufsize="7500k"),
        Rendition(name="720p", width=1280, height=720, video_bitrate="2800k", audio_bitrate="160k", maxrate="2996k", bufsize="4200k"),
    ])
    text = master.read_text()
    assert "#EXTM3U" in text
    assert "1080p/index.m3u8" in text
    assert "720p/index.m3u8" in text
