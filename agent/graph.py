from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import planner_prompt, architect_prompt, coder_system_prompt
from agent.states import Plan, TaskPlan, CoderState
from agent.tools import write_file, read_file, get_current_directory, list_files

_ = load_dotenv()

# Model pool — tries each in order if one hits rate limit
MODEL_POOL = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
]

def get_llm(model: str) -> ChatGroq:
    return ChatGroq(model=model, max_tokens=8192)

def invoke_with_fallback(fn, *args, **kwargs):
    """Try each model in the pool until one works."""
    last_error = None
    for model in MODEL_POOL:
        try:
            llm = get_llm(model)
            return fn(llm, *args, **kwargs)
        except Exception as e:
            if "rate_limit" in str(e) or "429" in str(e) or "decommissioned" in str(e):
                print(f"Model {model} failed: {e}. Trying next...")
                last_error = e
                continue
            raise e
    raise last_error


def planner_agent(state: dict) -> dict:
    def run(llm):
        resp = llm.with_structured_output(Plan).invoke(planner_prompt(state["user_prompt"]))
        if resp is None:
            raise ValueError("Planner returned None.")
        return {"plan": resp}
    return invoke_with_fallback(run)


def architect_agent(state: dict) -> dict:
    plan: Plan = state["plan"]
    def run(llm):
        try:
            resp = llm.with_structured_output(TaskPlan).invoke(
                architect_prompt(plan=plan.model_dump_json())
            )
        except Exception:
            resp = llm.with_structured_output(TaskPlan).invoke(
                architect_prompt(plan=plan.model_dump_json()) +
                "\n\nIMPORTANT: Return MAXIMUM 3 steps only."
            )
        if resp is None:
            raise ValueError("Architect returned None.")
        resp.plan = plan
        return {"task_plan": resp}
    return invoke_with_fallback(run)


def coder_agent(state: dict) -> dict:
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    user_prompt = (
        f"Write the complete content for '{current_task.filepath}'.\n\n"
        f"Task: {current_task.task_description}\n\n"
        f"IMPORTANT: You MUST call the write_file tool with:\n"
        f"  path = '{current_task.filepath}'\n"
        f"  content = the complete file content\n\n"
        f"Do NOT describe the code. Do NOT explain anything. "
        f"Just call write_file immediately with the full code as the content argument. "
        f"The content must be the raw file content only — no markdown, no backticks, no explanation."
    )

    def run(llm):
        coder_tools = [read_file, write_file, list_files, get_current_directory]
        react_agent = create_react_agent(llm, coder_tools)
        react_agent.invoke({
            "messages": [
                {"role": "system", "content": coder_system_prompt()},
                {"role": "user",   "content": user_prompt}
            ]
        })

    try:
        invoke_with_fallback(run)
    except Exception as e:
        print(f"Coder step {coder_state.current_step_idx} failed on all models: {e}")

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph = StateGraph(dict)
graph.add_node("planner",   planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder",     coder_agent)

graph.add_edge("planner",   "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()