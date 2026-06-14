"""
CodeAudit LangGraph Pipeline
START → detect_language → [security + quality + performance in parallel] → fix → score → END
"""
import uuid
import concurrent.futures
from langgraph.graph import StateGraph, END
from agents.state import CodeAuditState
from agents.language_detector import language_detector_node
from agents.security_agent import security_agent
from agents.quality_performance_agents import quality_agent, performance_agent
from agents.fix_scorer import fix_agent, scorer_node


def parallel_audit_node(state: CodeAuditState) -> CodeAuditState:
    """Run security, quality, performance agents in parallel."""
    updated = state.copy()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_sec  = ex.submit(security_agent, updated)
        f_qual = ex.submit(quality_agent, updated)
        f_perf = ex.submit(performance_agent, updated)
        sec_state  = f_sec.result(timeout=90)
        qual_state = f_qual.result(timeout=90)
        perf_state = f_perf.result(timeout=90)

    return {
        **updated,
        "security_issues":    sec_state.get("security_issues", []),
        "quality_issues":     qual_state.get("quality_issues", []),
        "performance_issues": perf_state.get("performance_issues", []),
    }


def build_graph():
    g = StateGraph(CodeAuditState)
    g.add_node("detect_language", language_detector_node)
    g.add_node("parallel_audit", parallel_audit_node)
    g.add_node("fix", fix_agent)
    g.add_node("score", scorer_node)

    g.set_entry_point("detect_language")
    g.add_edge("detect_language", "parallel_audit")
    g.add_edge("parallel_audit", "fix")
    g.add_edge("fix", "score")
    g.add_edge("score", END)
    return g.compile()


codeaudit_graph = build_graph()


def run_audit(
    code: str,
    filename: str = "code.py",
    session_id: str = None,
) -> dict:
    """Run complete code audit pipeline."""
    initial: CodeAuditState = {
        "messages": [],
        "session_id": session_id or uuid.uuid4().hex[:8],
        "code": code,
        "filename": filename,
        "language": "",
        "security_issues": [],
        "quality_issues": [],
        "performance_issues": [],
        "fixed_code": None,
        "diff_summary": "",
        "security_score": 0.0,
        "quality_score": 0.0,
        "performance_score": 0.0,
        "overall_score": 0.0,
        "grade": "F",
        "final_report": None,
        "report_json": None,
        "error": None,
    }
    return codeaudit_graph.invoke(initial)
