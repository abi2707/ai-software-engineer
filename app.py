import os
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import agent

# Resolve base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure generated_project folder exists BEFORE mounting
generated_dir = os.path.join(BASE_DIR, "generated_project")
os.makedirs(generated_dir, exist_ok=True)

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

# Serve generated projects for preview
app.mount(
    "/preview",
    StaticFiles(directory=generated_dir),
    name="preview"
)


class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/", response_class=HTMLResponse)
def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Run LangGraph agent
        agent.invoke(
            {"user_prompt": request.user_prompt},
            {"recursion_limit": 100}
        )
    except Exception as e:
        return {
            "message": f"Agent error: {str(e)}",
            "preview_url": None,
            "download_url": None
        }

    # Validate files were created
    if not os.listdir(generated_dir):
        return {
            "message": "Coder did not generate files.",
            "preview_url": None,
            "download_url": None
        }

    # Create ZIP
    zip_base = os.path.join(BASE_DIR, "generated_project")
    zip_file_path = zip_base + ".zip"

    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    shutil.make_archive(zip_base, "zip", generated_dir)

    return {
        "message": "Project generated successfully ✅",
        "preview_url": "/preview/index.html",
        "download_url": "/download"
    }


@app.get("/download")
def download_project():
    zip_path = os.path.join(BASE_DIR, "generated_project.zip")

    if not os.path.exists(zip_path):
        return {"message": "Zip file not found."}

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="generated_project.zip"
    )