from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, validator


class File(BaseModel):
    path: str = Field(description="The path to the file to be created")
    purpose: str = Field(description="The purpose of the file")


class Plan(BaseModel):
    name: str = Field(description="The name of the app to be built")
    description: str = Field(description="A one-line description of the app")
    techstack: str = Field(description="Always: plain HTML, CSS, JS")
    features: list[str] = Field(description="List of features")
    files: list[File] = Field(description="List of files — max 3: index.html, style.css, script.js")


class ImplementationTask(BaseModel):
    filepath: str = Field(description="Path to the file — must be index.html, style.css, or script.js")
    task_description: str = Field(description="Concise task description under 100 words")


class TaskPlan(BaseModel):
    implementation_steps: list[ImplementationTask] = Field(
        description="Ordered implementation steps. Maximum 3."
    )
    model_config = ConfigDict(extra="allow")

    @validator("implementation_steps")
    def limit_steps(cls, v):
        return v[:3]


class CoderState(BaseModel):
    task_plan: TaskPlan = Field(description="The plan to implement")
    current_step_idx: int = Field(0, description="Current step index")
    current_file_content: Optional[str] = Field(None, description="Current file content")