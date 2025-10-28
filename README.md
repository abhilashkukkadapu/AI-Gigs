### Video AI + Media Management (FFmpeg, HLS, AI CV, EDL/FCPXML, Scalable)

This project showcases:
- FFmpeg-driven transcoding and HLS packaging
- AI/CV modules (scene cut and face detection)
- Media asset management with timeline model
- Professional exports: EDL and FCPXML
- Scalable API + worker architecture with Redis/RQ
- Minimal React UI for upload, list, stream, export

### Architecture
- **API**: FastAPI (`backend/api/app.py`) for upload, process, stream, export.
- **Worker**: RQ worker (`backend/worker/jobs.py`) runs transcoding and AI tasks.
- **Core**: FFmpeg utils and storage (`backend/videoai/core/*`).
- **AI**: Scene and face detection (`backend/videoai/ai/*`).
- **Timeline**: Model + EDL/FCPXML exporters (`backend/videoai/timeline/*`).
- **Web**: React/Vite UI (`web/`).
- **Infra**: Dockerfiles and compose for `api`, `worker`, `redis`, `web` (`docker/`).

### Run locally (Python)
Prereqs: Python 3.11+, FFmpeg, Redis.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379/0
uvicorn backend.api.app:app --reload
# In another shell (optional, for async): rq worker -u $REDIS_URL video
```

Open `http://localhost:8000/docs` for API.

### Run with Docker Compose
```bash
docker compose -f docker/docker-compose.yml up --build
```
- API: `http://localhost:8000`
- Web UI: `http://localhost:5173`

### Key API endpoints
- `POST /upload`: upload a video file
- `POST /process/{asset_id}`: transcode to HLS, detect scenes/faces, export EDL/FCPXML
- `GET /assets` and `GET /assets/{asset_id}`: list/read asset metadata
- `GET /stream/{asset_id}/master.m3u8`: stream HLS
- `GET /exports/{asset_id}/{kind}`: download `edl` or `fcpxml`

### Tests
```bash
pytest -q
```

### Notes on professional video standards
- HLS VOD playlists with rendition-specific playlists and master manifest.
- EDL export uses non-drop frame with 24fps timecode.
- FCPXML contains a minimal sequence and asset-clip references using seconds timebase.

### Migration-ready architecture
- Client-heavy workflows (local editing, manual exports) are modeled server-side:
  - Upload to server storage, background workers perform compute-heavy tasks
  - Stateless API orchestrates jobs; Redis/RQ scales horizontally
  - Frontend is thin: upload + monitor + playback + download

