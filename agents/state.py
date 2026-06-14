"""CodeAudit LangGraph State"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class SecurityIssue(TypedDict):
    severity: str          # critical | high | medium | low | info
    owasp_id: str          # e.g. A03:2021
    owasp_name: str        # e.g. Injection
    line: Optional[int]
    description: str
    vulnerable_code: str
    fix: str
    cve: Optional[str]


class QualityIssue(TypedDict):
    severity: str          # high | medium | low
    category: str          # naming | complexity | duplication | solid | documentation
    line: Optional[int]
    description: str
    suggestion: str


class PerformanceIssue(TypedDict):
    severity: str          # high | medium | low
    category: str          # time_complexity | space_complexity | memory_leak | n_plus_one | blocking
    line: Optional[int]
    description: str
    current_complexity: str
    optimized_complexity: str
    fix: str


class CodeAuditState(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str

    # Input
    code: str
    filename: str
    language: str

    # Agent outputs
    security_issues: list[SecurityIssue]
    quality_issues: list[QualityIssue]
    performance_issues: list[PerformanceIssue]

    # Fix agent
    fixed_code: Optional[str]
    diff_summary: str

    # Scoring
    security_score: float       # 0-100
    quality_score: float
    performance_score: float
    overall_score: float
    grade: str                  # A+ A B+ B C D F

    # Report
    final_report: Optional[str]
    report_json: Optional[dict]

    # Control
    error: Optional[str]
