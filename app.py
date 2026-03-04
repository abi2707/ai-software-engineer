import os
import re
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import agent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.join(BASE_DIR, "generated_project")

# Create the folder before FastAPI tries to mount it
os.makedirs(PROJECT_FOLDER, exist_ok=True)

app = FastAPI(title="AI Software Engineer", version="1.0")

# Now safe to mount since folder is guaranteed to exist
app.mount("/static", StaticFiles(directory=PROJECT_FOLDER), name="static")

class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r") as f:
        return f.read()


@app.get("/debug")
def debug():
    return {
        "BASE_DIR": BASE_DIR,
        "project_folder_exists": os.path.exists(PROJECT_FOLDER),
        "files": os.listdir(PROJECT_FOLDER) if os.path.exists(PROJECT_FOLDER) else []
    }


def inline_assets(html: str, project_folder: str) -> str:
    def replace_css(match):
        path = os.path.join(project_folder, match.group(1))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f"<style>{f.read()}</style>"
        return match.group(0)

    def replace_js(match):
        path = os.path.join(project_folder, match.group(1))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                js = f.read()
            return f"<script>document.addEventListener('DOMContentLoaded',function(){{{js}}});</script>"
        return match.group(0)

    html = re.sub(r'<link[^>]+href=["\']([^"\']+\.css)["\'][^>]*>',
                  replace_css, html, flags=re.IGNORECASE)
    html = re.sub(r'<script[^>]*src=["\']([^"\'#][^"\']*\.js)["\'][^>]*>\s*</script>',
                  replace_js, html, flags=re.IGNORECASE)
    return html


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        agent.invoke({"user_prompt": request.user_prompt}, {"recursion_limit": 100})
    except Exception as e:
        return {"message": f"Agent error: {str(e)}", "preview_html": None, "download_url": None}

    zip_base = os.path.join(BASE_DIR, "generated_project")
    if os.path.exists(zip_base + ".zip"):
        os.remove(zip_base + ".zip")
    shutil.make_archive(zip_base, "zip", PROJECT_FOLDER)

    preview_html = None
    preview_path = os.path.join(PROJECT_FOLDER, "index.html")
    if os.path.exists(preview_path):
        with open(preview_path, "r", encoding="utf-8") as f:
            preview_html = inline_assets(f.read(), PROJECT_FOLDER)

    return {
        "message": "Project generated successfully",
        "preview_html": preview_html,
        "download_url": "/download"
    }


@app.get("/download")
def download_project():
    return FileResponse(
        os.path.join(BASE_DIR, "generated_project.zip"),
        media_type="application/zip",
        filename="generated_project.zip"
    )