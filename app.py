import os
import shutil
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import your LangGraph agent
from agent.graph import agent

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

# Template setup
templates = Jinja2Templates(directory="templates")


# -----------------------------
# Request Model
# -----------------------------
class ChatRequest(BaseModel):
    user_prompt: str


# -----------------------------
# Serve UI Homepage
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------
# Chat Endpoint
# -----------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = agent.invoke(
            {"user_prompt": request.user_prompt},
            {"recursion_limit": 100}
        )

        project_folder = "generated_project"
        zip_file_path = "generated_project.zip"

        if not os.path.exists(project_folder):
            return {"message": "Project folder not created ❌"}

        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        shutil.make_archive("generated_project", "zip", project_folder)

        return {
            "message": "Project generated successfully ✅",
            "download_url": "/download"
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {"message": f"Backend error: {str(e)}"}


# -----------------------------
# Download Endpoint
# -----------------------------
@app.get("/download")
def download_project():
    return FileResponse(
        path="generated_project.zip",
        media_type="application/zip",
        filename="generated_project.zip"
    )