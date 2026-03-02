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

        if not isinstance(result, dict) or "implementation_steps" not in result:
            return {"message": "Invalid agent response"}

        # Create project folder
        project_folder = "generated_project"

        if os.path.exists(project_folder):
            shutil.rmtree(project_folder)

        os.makedirs(project_folder)

        # Generate files from plan
        for file in result["plan"]["files"]:
            filepath = os.path.join(project_folder, file["path"])

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Generate simple placeholder content
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"<!-- {file['purpose']} -->\n")
                f.write(f"<h1>{result['plan']['name']}</h1>\n")

        # Create zip
        zip_path = shutil.make_archive("generated_project", "zip", project_folder)

        # Try to load index.html for preview
        index_path = os.path.join(project_folder, "index.html")
        preview_html = ""

        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                preview_html = f.read()
        else:
            preview_html = "<h2>Preview unavailable</h2>"

        return {
            "message": "Project generated successfully ✅",
            "preview_html": preview_html,
            "download_url": "/download"
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