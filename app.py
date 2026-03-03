import os
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent.graph import agent

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/")
def home():
    return {"status": "AI Software Engineer Running 🚀"}


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

    return {
        "message": "Project generated successfully ✅",
        "download_url": "/download"
    }


@app.get("/download")
def download_project():
    return FileResponse(
        "generated_project.zip",
        media_type="application/zip",
        filename="generated_project.zip"
    )