import os
import shutil
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import agent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

generated_dir = os.path.join(BASE_DIR, "generated_project")
os.makedirs(generated_dir, exist_ok=True)

app = FastAPI(
    title="AI Software Engineer",
    description="AI chatbot that converts prompts into working software projects.",
    version="1.0"
)

# Serve generated project as static preview
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

    # 🔥 1. Clear previous build completely
    for filename in os.listdir(generated_dir):
        file_path = os.path.join(generated_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            shutil.rmtree(file_path)

    # 🔥 2. Run agent
    try:
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

    # 🔥 3. Validate index.html exists
    index_path = os.path.join(generated_dir, "index.html")

    if not os.path.exists(index_path):
        return {
            "message": "Generation failed: index.html not created.",
            "preview_url": None,
            "download_url": None
        }

    # 🔥 4. Create zip
    zip_base = os.path.join(BASE_DIR, "generated_project")
    zip_path = zip_base + ".zip"

    if os.path.exists(zip_path):
        os.remove(zip_path)

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