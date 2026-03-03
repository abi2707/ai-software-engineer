import os
import re
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from agent.graph import agent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r") as f:
        return f.read()


@app.get("/debug")
def debug():
    project_folder = os.path.join(BASE_DIR, "generated_project")
    return {
        "BASE_DIR": BASE_DIR,
        "cwd": os.getcwd(),
        "project_folder_exists": os.path.exists(project_folder),
        "files": os.listdir(project_folder) if os.path.exists(project_folder) else []
    }


def inline_assets(html: str, project_folder: str) -> str:

    def replace_css(match):
        href = match.group(1)
        css_path = os.path.join(project_folder, href)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f"<style>{f.read()}</style>"
        return match.group(0)

    def replace_js(match):
        src = match.group(1)
        js_path = os.path.join(project_folder, src)
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as f:
                js = f.read()
            # Wrap in DOMContentLoaded to preserve defer behaviour
            return f"<script>document.addEventListener('DOMContentLoaded',function(){{{js}}});</script>"
        return match.group(0)

    # Inline CSS — handles all <link> variants
    html = re.sub(
        r'<link[^>]+href=["\']([^"\']+\.css)["\'][^>]*>',
        replace_css, html, flags=re.IGNORECASE
    )

    # Inline JS — handles defer, async, type="module", etc.
    html = re.sub(
        r'<script[^>]*src=["\']([^"\'#][^"\']*\.js)["\'][^>]*>\s*</script>',
        replace_js, html, flags=re.IGNORECASE
    )

    return html


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        agent.invoke(
            {"user_prompt": request.user_prompt},
            {"recursion_limit": 100}
        )
    except Exception as e:
        return {
            "message": f"Agent error: {str(e)}",
            "preview_html": None,
            "download_url": None
        }

    project_folder = os.path.join(BASE_DIR, "generated_project")
    zip_base = os.path.join(BASE_DIR, "generated_project")
    zip_file_path = zip_base + ".zip"

    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    shutil.make_archive(zip_base, "zip", project_folder)

    preview_html = None
    preview_path = os.path.join(project_folder, "index.html")
    if os.path.exists(preview_path):
        with open(preview_path, "r", encoding="utf-8") as f:
            raw_html = f.read()
        preview_html = inline_assets(raw_html, project_folder)

    return {
        "message": "Project generated successfully",
        "preview_html": preview_html,
        "download_url": "/download"
    }


@app.get("/download")
def download_project():
    zip_path = os.path.join(BASE_DIR, "generated_project.zip")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="generated_project.zip"
    )