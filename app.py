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

        # Assume your agent creates index.html inside generated_project
        file_path = "generated_project/index.html"

        if not os.path.exists(file_path):
            return {"message": "No preview file generated ❌"}

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return {
            "message": "Project generated successfully ✅",
            "preview_html": html_content
        }

    except Exception as e:
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