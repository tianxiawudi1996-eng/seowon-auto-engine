"""
SEOWON-AUTO ENGINE — FastAPI 백엔드
웹앱 ↔ 파이프라인 브릿지
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json, uuid, asyncio
from datetime import datetime

app = FastAPI(title="SEOWON-AUTO ENGINE API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

JOBS: dict = {}  # 실행 중인 작업 상태
ROOT = Path(__file__).parent.parent

class VideoRequest(BaseModel):
    channel: str   # seowon | jusi | unspoken
    topic: str
    action: str = "full"  # full | scout_only | benchmark

class JobStatus(BaseModel):
    job_id: str
    status: str    # queued | running | done | error
    channel: str
    topic: str
    progress: int  # 0~100
    current_stage: str
    output_path: str = ""
    created_at: str

@app.post("/api/generate")
async def generate_video(req: VideoRequest, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        "job_id": job_id, "status": "queued",
        "channel": req.channel, "topic": req.topic,
        "progress": 0, "current_stage": "대기 중",
        "output_path": "", "created_at": datetime.now().isoformat()
    }
    bg.add_task(run_pipeline, job_id, req.channel, req.topic, req.action)
    return {"job_id": job_id, "message": "파이프라인 시작됨"}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "작업 없음")
    return JOBS[job_id]

@app.get("/api/jobs")
async def list_jobs():
    return list(JOBS.values())

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    if job_id in JOBS:
        JOBS[job_id]["status"] = "cancelled"
    return {"cancelled": job_id}

async def run_pipeline(job_id: str, channel: str, topic: str, action: str):
    stages = [
        (10, "Scout: 레퍼런스 수집 중"),
        (25, "Strategist: 컨셉 전략 수립"),
        (45, "Script: 대본 작성 중"),
        (60, "Visual: 씬 설계 중"),
        (72, "TTS: 음성 생성 중"),
        (80, "Subtitle: 자막 생성"),
        (90, "CapCut: 편집 JSON 생성"),
        (95, "QA: 품질 검수"),
        (100, "Publisher: YouTube 업로드"),
    ]
    try:
        JOBS[job_id]["status"] = "running"
        from src.orchestrator import SeowonAutoEngine
        for prog, stage in stages:
            JOBS[job_id]["progress"] = prog
            JOBS[job_id]["current_stage"] = stage
            await asyncio.sleep(2)
        engine = SeowonAutoEngine(channel, topic, action)
        engine.run()
        JOBS[job_id].update({"status": "done", "progress": 100,
            "current_stage": "완료!", "output_path": str(ROOT / "output")})
    except Exception as e:
        JOBS[job_id].update({"status": "error", "current_stage": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
