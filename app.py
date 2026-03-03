from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import zipfile

app = FastAPI()

# Serve generated project as real static site
app.mount(
    "/generated",
    StaticFiles(directory="generated_project"),
    name="generated"
)

class ChatRequest(BaseModel):
    user_prompt: str


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
def chat(req: ChatRequest):

    os.makedirs("generated_project", exist_ok=True)

    # === SAMPLE GENERATED PROJECT ===
    # (Replace this later with your agent output)

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Generated App</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <h1>Hello from Buildy 🚀</h1>
        <button onclick="hello()">Click Me</button>
        <script src="script.js"></script>
    </body>
    </html>
    """

    css_content = """
    body {
        font-family: Arial;
        text-align: center;
        margin-top: 100px;
        background: #f4f4f4;
    }
    button {
        padding: 10px 20px;
        font-size: 16px;
    }
    """

    js_content = """
    function hello() {
        alert("Preview is fully functional!");
    }
    """

    with open("generated_project/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    with open("generated_project/style.css", "w", encoding="utf-8") as f:
        f.write(css_content)

    with open("generated_project/script.js", "w", encoding="utf-8") as f:
        f.write(js_content)

    # Create ZIP
    zip_path = "generated_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, dirs, files in os.walk("generated_project"):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, "generated_project")
                zipf.write(full_path, rel_path)

    return JSONResponse({
        "message": "Project generated successfully",
        "preview_html": None,  # IMPORTANT: we don't use srcdoc anymore
        "download_url": "/download"
    })


@app.get("/download")
def download():
    return FileResponse(
        "generated_project.zip",
        media_type="application/zip",
        filename="project.zip"
    )