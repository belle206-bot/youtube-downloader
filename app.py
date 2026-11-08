"""
YouTube 다운로더 웹 서비스 백엔드 (FastAPI)
"""
import os
import sys
import uuid
import threading
import subprocess
import urllib.parse
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import downloader

app = FastAPI(title="YouTube Video Downloader")

# 기본 다운로드 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

# 템플릿 설정
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 다운로드 작업 관리
# task_id -> { status, percent, speed, eta, filename, error, title, output_dir }
tasks: Dict[str, Dict[str, Any]] = {}
current_config = {
    "download_dir": DEFAULT_DOWNLOAD_DIR
}

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    download_dir: Optional[str] = None

class FolderRequest(BaseModel):
    path: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"default_dir": current_config["download_dir"]}
    )

@app.post("/api/info")
async def get_info(payload: InfoRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 링크를 입력해주세요.")
    try:
        info = downloader.get_video_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"영상 정보를 가져올 수 없습니다: {str(e)}")

def run_download_task(task_id: str, url: str, target_dir: str, quality: str):
    tasks[task_id]["status"] = "downloading"
    tasks[task_id]["percent"] = 0.0
    
    def on_progress(p):
        tasks[task_id]["status"] = p.get("status", "downloading")
        tasks[task_id]["percent"] = p.get("percent", 0.0)
        tasks[task_id]["speed"] = p.get("speed", "")
        tasks[task_id]["eta"] = p.get("eta", "")
        if p.get("filename"):
            tasks[task_id]["filename"] = p.get("filename")

    try:
        result = downloader.download_video(url, target_dir, quality, on_progress)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["percent"] = 100.0
        tasks[task_id]["result"] = result
        tasks[task_id]["filename"] = result["file_name"]
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

@app.post("/api/download")
async def start_download(payload: DownloadRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 링크를 입력해주세요.")
    
    target_dir = payload.download_dir.strip() if payload.download_dir else current_config["download_dir"]
    os.makedirs(target_dir, exist_ok=True)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "url": url,
        "quality": payload.quality,
        "download_dir": target_dir,
        "status": "pending",
        "percent": 0.0,
        "speed": "",
        "eta": "",
        "filename": "",
        "error": None,
        "result": None
    }
    
    # 별도 스레드에서 다운로드 실행
    thread = threading.Thread(
        target=run_download_task,
        args=(task_id, url, target_dir, payload.quality),
        daemon=True
    )
    thread.start()
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/download-file/{filename}")
async def download_file_to_browser(filename: str):
    """외부 접속 사용자가 브라우저를 통해 직접 본인 기기로 파일을 다운로드하도록 지원"""
    # 안전한 파일 경로 확인 (디렉토리 탈출 방지)
    safe_filename = os.path.basename(filename)
    target_path = os.path.join(current_config["download_dir"], safe_filename)
    
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
    encoded_filename = urllib.parse.quote(safe_filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    media_type = "audio/mpeg" if safe_filename.endswith(".mp3") else "video/mp4"
    return FileResponse(target_path, media_type=media_type, headers=headers)

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return tasks[task_id]

@app.get("/api/downloads")
async def list_downloads():
    target_dir = current_config["download_dir"]
    if not os.path.exists(target_dir):
        return {"files": []}
        
    allowed_exts = {'.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.wav', '.flac'}
    files_info = []
    
    try:
        with os.scandir(target_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    _, ext = os.path.splitext(entry.name)
                    if ext.lower() in allowed_exts:
                        stat = entry.stat()
                        size_mb = round(stat.st_size / (1024 * 1024), 2)
                        files_info.append({
                            "name": entry.name,
                            "size": f"{size_mb} MB",
                            "size_bytes": stat.st_size,
                            "modified": stat.st_mtime,
                            "path": entry.path
                        })
        # 최신 수정순 정렬
        files_info.sort(key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        return {"files": [], "error": str(e)}

    return {"files": files_info, "folder": target_dir}

@app.post("/api/open-folder")
async def open_folder(payload: FolderRequest):
    folder = payload.path if payload.path else current_config["download_dir"]
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    
    try:
        # 윈도우 탐색기 열기
        os.startfile(folder)
        return {"status": "success", "message": f"폴더를 열었습니다: {folder}"}
    except Exception as e:
        # 백업 방식
        try:
            subprocess.run(["explorer", folder], check=False)
            return {"status": "success", "message": f"탐색기를 실행했습니다: {folder}"}
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"폴더를 열 수 없습니다: {str(ex)}")

@app.post("/api/choose-folder-dialog")
async def choose_folder_dialog():
    """Windows 폴더 선택 GUI 팝업 실행"""
    def pick_folder():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            selected = filedialog.askdirectory(initialdir=current_config["download_dir"])
            root.destroy()
            return selected
        except Exception:
            return None

    # 별도 스레드에서 다이얼로그 호출 (메인 루프 차단 방지)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(pick_folder)
        selected_folder = future.result()

    if selected_folder:
        selected_folder = os.path.normpath(selected_folder)
        current_config["download_dir"] = selected_folder
        return {"status": "selected", "path": selected_folder}
    return {"status": "cancelled", "path": current_config["download_dir"]}

@app.post("/api/set-folder")
async def set_folder(payload: FolderRequest):
    if not payload.path:
        raise HTTPException(status_code=400, detail="폴더 경로를 입력하세요.")
    norm_path = os.path.normpath(payload.path.strip())
    os.makedirs(norm_path, exist_ok=True)
    current_config["download_dir"] = norm_path
    return {"status": "success", "download_dir": norm_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=False)
