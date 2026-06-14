"""
Fix Agent — generates fixed code
Scorer — computes security/quality/performance scores and grade
"""
import re
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import CodeAuditState
from utils.config import invoke_llm

FIX_SYSTEM = """You are an expert software engineer. Fix ALL the identified issues in the code.

Rules:
- Fix every critical and high severity issue
- Preserve the original logic and functionality
- Add inline comments explaining each fix
- Return the complete fixed file, not just snippets

Return ONLY valid JSON:
{
  "fixed_code": "complete fixed code here",
  "changes": [
    "Fixed SQL injection on line 15 — used parameterized query",
    "Replaced eval() with ast.literal_eval()"
  ]
}
Return ONLY JSON."""

REPORT_SYSTEM = """You are a senior code reviewer. Write a concise executive summary of this code audit.
Return ONLY valid JSON:
{
  "executive_summary": "2-3 sentence overview",
  "top_risks": ["risk1", "risk2", "risk3"],
  "quick_wins": ["easy fix 1", "easy fix 2"],
  "recommendation": "Ship with fixes | Needs major rework | Do not ship"
}"""


def fix_agent(state: CodeAuditState) -> CodeAuditState:
    """Generate fixed code addressing all identified issues."""
    code = state["code"]
    lang = state.get("language", "unknown")
    sec = state.get("security_issues", [])
    qual = state.get("quality_issues", [])
    perf = state.get("performance_issues", [])

    critical = [i for i in sec if i.get("severity") in ("critical", "high")]
    if not critical and not qual and not perf:
        return {**state, "fixed_code": code, "diff_summary": "No issues found — code is clean."}

    issues_summary = "\n".join(
        f"- [{i.get('severity','?').upper()}] {i.get('description','')} → Fix: {i.get('fix','')}"
        for i in (sec + qual + perf)[:15]
    )

    prompt = (
        f"Language: {lang}\n\n"
        f"Original code:\n```{lang}\n{code[:2500]}\n```\n\n"
        f"Issues to fix:\n{issues_summary}\n\n"
        "Return the complete fixed code as JSON."
    )

    try:
        raw = invoke_llm(
            [SystemMessage(content=FIX_SYSTEM), HumanMessage(content=prompt)],
            temperature=0.1, max_tokens=2048,
        )
        raw = re.sub(r'```(?:json)?|```', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group() if match else raw)
        fixed = result.get("fixed_code", code)
        changes = result.get("changes", [])
        diff_summary = "\n".join(f"• {c}" for c in changes)
    except Exception as e:
        print(f"[Fix] Error: {e}")
        fixed = code
        # Build manual fix guide from issues
        manual = ["Auto-fix could not generate code. Apply these fixes manually:"]
        for issue in (sec + qual + perf)[:8]:
            fix_text = issue.get("fix", issue.get("suggestion", ""))
            if fix_text:
                manual.append(f"• [{issue.get('severity','?').upper()}] {fix_text}")
        diff_summary = "\n".join(manual)

    return {**state, "fixed_code": fixed, "diff_summary": diff_summary}


def scorer_node(state: CodeAuditState) -> CodeAuditState:
    """Compute scores and generate final report."""
    sec_issues = state.get("security_issues", [])
    qual_issues = state.get("quality_issues", [])
    perf_issues = state.get("performance_issues", [])

    # Security score (most punishing)
    sec_deductions = {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 1}
    sec_score = max(0, 100 - sum(sec_deductions.get(i.get("severity","info"), 1) for i in sec_issues))

    # Quality score
    qual_deductions = {"high": 12, "medium": 6, "low": 2}
    qual_score = max(0, 100 - sum(qual_deductions.get(i.get("severity","low"), 2) for i in qual_issues))

    # Performance score
    perf_deductions = {"high": 15, "medium": 8, "low": 3}
    perf_score = max(0, 100 - sum(perf_deductions.get(i.get("severity","low"), 3) for i in perf_issues))

    # Weighted overall (security counts most)
    overall = sec_score * 0.5 + qual_score * 0.3 + perf_score * 0.2

    # Grade
    grade = ("A+" if overall >= 95 else "A" if overall >= 90 else "B+" if overall >= 85
             else "B" if overall >= 80 else "C+" if overall >= 75 else "C" if overall >= 70
             else "D" if overall >= 60 else "F")

    # LLM executive summary
    code = state.get("code", "")
    lang = state.get("language", "unknown")
    issues_text = (
        f"Security issues: {len(sec_issues)} ({sum(1 for i in sec_issues if i.get('severity') in ('critical','high'))} critical/high)\n"
        f"Quality issues: {len(qual_issues)}\n"
        f"Performance issues: {len(perf_issues)}\n"
        f"Scores: Security={sec_score:.0f} Quality={qual_score:.0f} Performance={perf_score:.0f} Overall={overall:.0f}"
    )
    try:
        raw = invoke_llm(
            [SystemMessage(content=REPORT_SYSTEM),
             HumanMessage(content=f"Language: {lang}\n\nAudit summary:\n{issues_text}\n\nCode snippet:\n{code[:800]}")],
            temperature=0.2, max_tokens=400,
        )
        raw = re.sub(r'```(?:json)?|```', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        exec_data = json.loads(match.group() if match else raw)
    except Exception:
        exec_data = {"executive_summary": "Automated audit complete.",
                     "top_risks": [], "quick_wins": [], "recommendation": "Review issues above"}

    # Build markdown report
    report = _build_report(state, sec_score, qual_score, perf_score, overall, grade, exec_data)

    report_json = {
        "language": lang,
        "overall_score": round(overall, 1),
        "grade": grade,
        "security_score": round(sec_score, 1),
        "quality_score": round(qual_score, 1),
        "performance_score": round(perf_score, 1),
        "total_issues": len(sec_issues) + len(qual_issues) + len(perf_issues),
        "security_issues": sec_issues,
        "quality_issues": qual_issues,
        "performance_issues": perf_issues,
        "executive_summary": exec_data.get("executive_summary", ""),
        "recommendation": exec_data.get("recommendation", ""),
    }

    print(f"[Scorer] Grade: {grade} | Overall: {overall:.0f} | "
          f"Sec:{sec_score:.0f} Qual:{qual_score:.0f} Perf:{perf_score:.0f}")

    return {
        **state,
        "security_score": sec_score,
        "quality_score": qual_score,
        "performance_score": perf_score,
        "overall_score": overall,
        "grade": grade,
        "final_report": report,
        "report_json": report_json,
    }


def _build_report(state, sec_score, qual_score, perf_score, overall, grade, exec_data) -> str:
    lang = state.get("language", "unknown")
    sec = state.get("security_issues", [])
    qual = state.get("quality_issues", [])
    perf = state.get("performance_issues", [])
    diff = state.get("diff_summary", "")
    filename = state.get("filename", "code")

    sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️",
                  "high": "🟠"}

    lines = [
        f"# CodeAudit Report — {filename}",
        f"**Language:** {lang.upper()} | **Grade:** {grade} | **Overall Score:** {overall:.0f}/100\n",
        f"## Executive Summary\n{exec_data.get('executive_summary', '')}",
        f"**Recommendation:** {exec_data.get('recommendation', '')}",
    ]

    # Score cards
    lines.append(f"\n## Scores\n| Category | Score | Issues |\n|----------|-------|--------|\n"
                 f"| 🔒 Security | {sec_score:.0f}/100 | {len(sec)} |\n"
                 f"| ✨ Quality | {qual_score:.0f}/100 | {len(qual)} |\n"
                 f"| ⚡ Performance | {perf_score:.0f}/100 | {len(perf)} |\n"
                 f"| **Overall** | **{overall:.0f}/100** | **{len(sec)+len(qual)+len(perf)}** |")

    if sec:
        lines.append("\n## 🔒 Security Issues")
        for i in sec:
            e = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢","info":"ℹ️"}.get(i.get("severity","info"),"⚪")
            lines.append(f"\n### {e} [{i.get('severity','?').upper()}] {i.get('owasp_id','')} — {i.get('owasp_name','')}")
            lines.append(f"**Issue:** {i.get('description','')}")
            if i.get("vulnerable_code"):
                lines.append(f"```\n{i['vulnerable_code']}\n```")
            lines.append(f"**Fix:** {i.get('fix','')}")
            if i.get("cve"):
                lines.append(f"**CVE:** {i['cve']}")

    if qual:
        lines.append("\n## ✨ Quality Issues")
        for i in qual:
            e = {"high":"🟠","medium":"🟡","low":"🟢"}.get(i.get("severity","low"),"⚪")
            lines.append(f"\n### {e} [{i.get('severity','?').upper()}] {i.get('category','').replace('_',' ').title()}")
            lines.append(f"{i.get('description','')}\n**Suggestion:** {i.get('suggestion','')}")

    if perf:
        lines.append("\n## ⚡ Performance Issues")
        for i in perf:
            e = {"high":"🟠","medium":"🟡","low":"🟢"}.get(i.get("severity","low"),"⚪")
            lines.append(f"\n### {e} [{i.get('severity','?').upper()}] {i.get('category','').replace('_',' ').title()}")
            lines.append(f"{i.get('description','')}")
            if i.get("current_complexity"):
                lines.append(f"**Complexity:** {i['current_complexity']} → {i.get('optimized_complexity','?')}")
            lines.append(f"**Fix:** {i.get('fix','')}")

    if diff:
        lines.append(f"\n## 🔧 Auto-Fix Applied\n{diff}")

    top_risks = exec_data.get("top_risks", [])
    if top_risks:
        lines.append("\n## Top Risks\n" + "\n".join(f"- {r}" for r in top_risks))

    quick_wins = exec_data.get("quick_wins", [])
    if quick_wins:
        lines.append("\n## Quick Wins\n" + "\n".join(f"- {w}" for w in quick_wins))

    lines.append("\n---\n*Generated by CodeAudit Agent — Nimra Tariq, Superior University Pakistan*")
    return "\n".join(lines)
