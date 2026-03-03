import os
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import agent

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r") as f:
        return f.read()


@app.post("/chat")
async def chat(request: ChatRequest):
    result = agent.invoke(
        {"user_prompt": request.user_prompt},
        {"recursion_limit": 100}
    )

    project_folder = "generated_project"
    zip_file_path = "generated_project.zip"

    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    shutil.make_archive("generated_project", "zip", project_folder)

    # Build a preview from the generated project's index.html (if it exists)
    preview_html = None
    preview_path = os.path.join(project_folder, "index.html")
    if os.path.exists(preview_path):
        with open(preview_path, "r") as f:
            preview_html = f.read()

    return {
        "message": "Project generated successfully ✅",
        "preview_html": preview_html,
        "download_url": "/download"
    }


@app.get("/download")
def download_project():
    return FileResponse(
        "generated_project.zip",
        media_type="application/zip",
        filename="generated_project.zip"
    )