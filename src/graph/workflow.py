from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from src.models.user import User
from src.parsers.file_parser import parse_file
from src.extraction.chain import extract_resume_info


class ResumeState(TypedDict):
    file_path: str
    raw_text: Optional[str]
    user: Optional[User]
    error: Optional[str]
    status: str


def _parse_node(state: ResumeState) -> ResumeState:
    try:
        raw_text = parse_file(state["file_path"])
        return {**state, "raw_text": raw_text, "status": "parsed"}
    except Exception as e:
        return {**state, "error": f"文件解析失败: {str(e)}", "status": "error"}


def _should_extract(state: ResumeState) -> str:
    if state.get("error"):
        return END
    if not state.get("raw_text", "").strip():
        return END
    return "extract"


def _extract_node(state: ResumeState) -> ResumeState:
    try:
        user = extract_resume_info(state["raw_text"])
        return {**state, "user": user, "status": "completed"}
    except Exception as e:
        return {**state, "error": f"信息提取失败: {str(e)}", "status": "error"}


def build_resume_workflow() -> StateGraph:
    workflow = StateGraph(ResumeState)

    workflow.add_node("parse", _parse_node)
    workflow.add_node("extract", _extract_node)

    workflow.set_entry_point("parse")
    workflow.add_conditional_edges("parse", _should_extract, {"extract": "extract", END: END})
    workflow.add_edge("extract", END)

    return workflow.compile()
