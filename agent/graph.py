from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import planner_prompt, architect_prompt, coder_system_prompt
from agent.states import Plan, TaskPlan, CoderState
from agent.tools import write_file, read_file, get_current_directory, list_files

_ = load_dotenv()

llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", max_tokens=8192)


def planner_agent(state: dict) -> dict:
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(planner_prompt(user_prompt))
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    plan: Plan = state["plan"]
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
        raise ValueError("Architect did not return a valid response.")
    resp.plan = plan
    return {"task_plan": resp}


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

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    try:
        react_agent.invoke({
            "messages": [
                {"role": "system", "content": coder_system_prompt()},
                {"role": "user",   "content": user_prompt}
            ]
        })
    except Exception as e:
        print(f"Coder step {coder_state.current_step_idx} failed: {e}")

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