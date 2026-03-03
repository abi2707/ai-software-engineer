import os
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import agent

# Always resolve paths relative to this file, not the working directory
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
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r") as f:
        return f.read()


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = agent.invoke(
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
    print("Project folder path:", project_folder)
    if os.path.exists(project_folder):
        print("Files inside generated_project:", os.listdir(project_folder))
    else:
        print("generated_project folder does NOT exist")

    zip_base = os.path.join(BASE_DIR, "generated_project")
    zip_file_path = zip_base + ".zip"
    
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    shutil.make_archive(zip_base, "zip", project_folder)

    # Read generated project's index.html for preview
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
    zip_path = os.path.join(BASE_DIR, "generated_project.zip")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="generated_project.zip"
    )