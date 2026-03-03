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
app.mount(
    "/preview",
    StaticFiles(directory=os.path.join(BASE_DIR, "generated_project")),
    name="preview"
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
            "preview_url": None,
            "download_url": None
        }

    project_folder = os.path.join(BASE_DIR, "generated_project")

    if not os.path.exists(project_folder) or not os.listdir(project_folder):
        return {
            "message": "Coder did not generate files.",
            "preview_url": None,
            "download_url": None
        }

    zip_base = os.path.join(BASE_DIR, "generated_project")
    zip_file_path = zip_base + ".zip"

    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    shutil.make_archive(zip_base, "zip", project_folder)

    return {
        "message": "Project generated successfully ✅",
        "preview_url": "/preview/index.html",
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