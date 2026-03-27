import time
import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from agents.monitoring_agent import run_monitoring
from agents.review_agent import run_review
from agents.roadmap_agent import run_roadmap_generation


class PipelineState(TypedDict):
    student_id: int
    api_key: str
    monitoring_output: str
    monitoring_steps: list
    review_output: str
    review_steps: list
    roadmap_output: str
    roadmap_steps: list
    skipped_review: bool
    errors: list


def monitoring_node(state: PipelineState) -> dict:
    print(f"\nSTAGE 1: Monitoring Agent for student {state['student_id']}")
    try:
        t0 = time.time()
        result = run_monitoring(state["student_id"], state["api_key"])
        print(f"Monitoring complete in {round(time.time() - t0, 1)}s")
        return {
            "monitoring_output": result["output"],
            "monitoring_steps": result["steps"],
        }
    except Exception as e:
        return {
            "monitoring_output": f"Monitoring failed: {str(e)}",
            "monitoring_steps": [],
            "errors": state.get("errors", []) + [{"agent": "monitoring", "error": str(e)}],
        }


def should_review(state: PipelineState) -> Literal["review", "roadmap"]:
    output = state.get("monitoring_output", "")
    try:
        data = json.loads(output) if output.startswith("{") else None
    except json.JSONDecodeError:
        data = None

    if data and data.get("adherence_score", 0) >= 90 and not data.get("should_escalate"):
        print("Adherence >= 90% and no escalation needed. Skipping review, going to roadmap.")
        return "roadmap"
    return "review"


def review_node(state: PipelineState) -> dict:
    print(f"\nSTAGE 2: Review Agent for student {state['student_id']}")
    prior_context = state.get("monitoring_output", "")
    try:
        t0 = time.time()
        result = run_review(state["student_id"], state["api_key"], prior_context=prior_context)
        print(f"Review complete in {round(time.time() - t0, 1)}s")
        return {
            "review_output": result["output"],
            "review_steps": result["steps"],
            "skipped_review": False,
        }
    except Exception as e:
        return {
            "review_output": f"Review failed: {str(e)}",
            "review_steps": [],
            "skipped_review": False,
            "errors": state.get("errors", []) + [{"agent": "review", "error": str(e)}],
        }


def roadmap_node(state: PipelineState) -> dict:
    print(f"\nSTAGE 3: Roadmap Agent for student {state['student_id']}")
    prior_parts = []
    if state.get("monitoring_output"):
        prior_parts.append(f"MONITORING FINDINGS:\n{state['monitoring_output']}")
    if state.get("review_output") and not state.get("skipped_review"):
        prior_parts.append(f"REVIEW SUMMARY:\n{state['review_output']}")
    prior_context = "\n\n".join(prior_parts)

    try:
        t0 = time.time()
        result = run_roadmap_generation(state["student_id"], state["api_key"], prior_context=prior_context)
        print(f"Roadmap complete in {round(time.time() - t0, 1)}s")
        return {
            "roadmap_output": result["output"],
            "roadmap_steps": result["steps"],
        }
    except Exception as e:
        return {
            "roadmap_output": f"Roadmap failed: {str(e)}",
            "roadmap_steps": [],
            "errors": state.get("errors", []) + [{"agent": "roadmap", "error": str(e)}],
        }


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("monitoring", monitoring_node)
    graph.add_node("review", review_node)
    graph.add_node("roadmap", roadmap_node)

    graph.add_edge(START, "monitoring")
    graph.add_conditional_edges("monitoring", should_review, {"review": "review", "roadmap": "roadmap"})
    graph.add_edge("review", "roadmap")
    graph.add_edge("roadmap", END)

    return graph.compile()


def run_full_pipeline(student_id, api_key):
    pipeline = build_pipeline()
    t0 = time.time()

    final_state = pipeline.invoke({
        "student_id": student_id,
        "api_key": api_key,
        "monitoring_output": "",
        "monitoring_steps": [],
        "review_output": "",
        "review_steps": [],
        "roadmap_output": "",
        "roadmap_steps": [],
        "skipped_review": False,
        "errors": [],
    })

    duration = round(time.time() - t0, 2)
    agents = {}

    if final_state.get("monitoring_output"):
        agents["monitoring"] = {
            "status": "error" if any(e["agent"] == "monitoring" for e in final_state.get("errors", [])) else "success",
            "output": final_state["monitoring_output"],
            "steps": final_state["monitoring_steps"],
        }
    if final_state.get("review_output") and not final_state.get("skipped_review"):
        agents["review"] = {
            "status": "error" if any(e["agent"] == "review" for e in final_state.get("errors", [])) else "success",
            "output": final_state["review_output"],
            "steps": final_state["review_steps"],
        }
    elif final_state.get("skipped_review"):
        agents["review"] = {"status": "skipped", "output": "Skipped: adherence >= 90% with no escalation needed", "steps": []}
    if final_state.get("roadmap_output"):
        agents["roadmap"] = {
            "status": "error" if any(e["agent"] == "roadmap" for e in final_state.get("errors", [])) else "success",
            "output": final_state["roadmap_output"],
            "steps": final_state["roadmap_steps"],
        }

    successful = sum(1 for a in agents.values() if a.get("status") == "success")
    print(f"\nPipeline complete: {successful}/{len(agents)} agents succeeded in {duration}s")

    return {
        "student_id": student_id,
        "agents": agents,
        "pipeline_duration_seconds": duration,
        "errors": final_state.get("errors", []),
        "summary": f"{successful}/{len(agents)} agents completed successfully",
    }


def run_single_agent(agent_type, student_id, api_key):
    runners = {"monitoring": run_monitoring, "review": run_review, "roadmap": run_roadmap_generation}
    if agent_type not in runners:
        return {"error": f"Unknown agent type: {agent_type}"}
    try:
        t0 = time.time()
        result = runners[agent_type](student_id, api_key)
        return {"agent": agent_type, "student_id": student_id, "status": "success", "output": result["output"], "steps": result["steps"], "duration_seconds": round(time.time() - t0, 2)}
    except Exception as e:
        return {"agent": agent_type, "student_id": student_id, "status": "error", "error": str(e)}
