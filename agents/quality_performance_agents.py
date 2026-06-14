"""
Quality Agent — clean code, SOLID principles, complexity
Performance Agent — Big-O, memory leaks, bottlenecks
"""
import re
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import CodeAuditState
from utils.config import invoke_llm

QUALITY_SYSTEM = """You are a senior software engineer and clean code expert.
Analyze code quality and return ONLY valid JSON:
{
  "issues": [
    {
      "severity": "high | medium | low",
      "category": "naming | complexity | duplication | solid | documentation | error_handling",
      "line": 10,
      "description": "Clear description",
      "suggestion": "How to fix it"
    }
  ],
  "metrics": {
    "cyclomatic_complexity": "low | medium | high",
    "maintainability": "good | fair | poor",
    "test_coverage_hints": ["what to test"]
  }
}

Check for:
- Meaningful variable/function names (not x, y, temp, data)
- Function length (>30 lines = too long)
- Cyclomatic complexity (>10 = too complex)
- Code duplication (DRY violations)
- SOLID principles violations
- Missing error handling
- Magic numbers/strings
- Dead code
- Inconsistent style
Return ONLY JSON."""

PERFORMANCE_SYSTEM = """You are a performance engineering expert.
Analyze code for performance issues and return ONLY valid JSON:
{
  "issues": [
    {
      "severity": "high | medium | low",
      "category": "time_complexity | space_complexity | memory_leak | n_plus_one | blocking | inefficient_loop",
      "line": 25,
      "description": "Performance issue description",
      "current_complexity": "O(n²)",
      "optimized_complexity": "O(n log n)",
      "fix": "How to optimize"
    }
  ],
  "overall_complexity": {
    "time": "O(n)",
    "space": "O(1)"
  }
}

Check for:
- Nested loops (O(n²) or worse)
- Sorting inside loops
- Database queries inside loops (N+1)
- Repeated expensive operations
- Memory leaks (unclosed resources)
- Blocking I/O without async
- Unnecessary list comprehensions creating large objects
- String concatenation in loops (use join)
- Missing caching for repeated computation
Return ONLY JSON."""


def quality_agent(state: CodeAuditState) -> CodeAuditState:
    """Analyze code quality."""
    code = state["code"]
    lang = state.get("language", "unknown")

    # Static checks
    static_issues = _static_quality_check(code)

    # LLM analysis
    try:
        raw = invoke_llm(
            [SystemMessage(content=QUALITY_SYSTEM),
             HumanMessage(content=f"Language: {lang}\n\nCode:\n```{lang}\n{code[:3000]}\n```")],
            temperature=0.1, max_tokens=1500,
        )
        raw = re.sub(r'```(?:json)?|```', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group() if match else raw)
        llm_issues = result.get("issues", [])
    except Exception as e:
        print(f"[Quality] LLM error: {e}")
        llm_issues = []

    all_issues = static_issues + llm_issues
    sev_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: sev_order.get(x.get("severity", "low"), 2))

    print(f"[Quality] Found {len(all_issues)} issues")
    return {**state, "quality_issues": all_issues}


def performance_agent(state: CodeAuditState) -> CodeAuditState:
    """Analyze performance issues."""
    code = state["code"]
    lang = state.get("language", "unknown")

    static_issues = _static_performance_check(code)

    try:
        raw = invoke_llm(
            [SystemMessage(content=PERFORMANCE_SYSTEM),
             HumanMessage(content=f"Language: {lang}\n\nCode:\n```{lang}\n{code[:3000]}\n```")],
            temperature=0.1, max_tokens=1500,
        )
        raw = re.sub(r'```(?:json)?|```', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group() if match else raw)
        llm_issues = result.get("issues", [])
    except Exception as e:
        print(f"[Performance] LLM error: {e}")
        llm_issues = []

    all_issues = static_issues + llm_issues
    sev_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: sev_order.get(x.get("severity", "low"), 2))

    print(f"[Performance] Found {len(all_issues)} issues")
    return {**state, "performance_issues": all_issues}


def _static_quality_check(code: str) -> list:
    """Fast static quality checks."""
    issues = []
    lines = code.split("\n")

    # Long functions
    in_func, func_start, func_lines = False, 0, 0
    for i, line in enumerate(lines):
        if re.match(r'\s*(def|function|func|void|public|private)\s+\w+', line):
            if in_func and func_lines > 40:
                issues.append({"severity": "medium", "category": "complexity",
                    "line": func_start, "description": f"Function is too long ({func_lines} lines). Split into smaller functions.",
                    "suggestion": "Keep functions under 30 lines. Single responsibility principle."})
            in_func, func_start, func_lines = True, i+1, 0
        elif in_func:
            func_lines += 1

    # Magic numbers
    magic = re.findall(r'(?<!\w)(?<!\.)\b(?!0|1|2|100)\d{2,}\b', code)
    if len(magic) > 3:
        issues.append({"severity": "low", "category": "naming",
            "line": None, "description": f"Magic numbers found: {', '.join(set(magic[:5]))}",
            "suggestion": "Replace magic numbers with named constants."})

    # Single letter variables (except loop counters)
    bad_names = re.findall(r'\b(?<![.])([a-z])\s*=\s*[^=]', code)
    bad_names = [n for n in bad_names if n not in ['i','j','k','x','y','n','e']]
    if bad_names:
        issues.append({"severity": "low", "category": "naming",
            "line": None, "description": f"Poor variable names: {', '.join(set(bad_names[:5]))}",
            "suggestion": "Use descriptive names that explain the variable's purpose."})

    return issues


def _static_performance_check(code: str) -> list:
    """Fast static performance checks."""
    issues = []

    # Nested loops
    loop_depth = 0
    for line in code.split("\n"):
        if re.match(r'\s*(for|while)\s+', line):
            loop_depth += 1
            if loop_depth >= 2:
                issues.append({"severity": "high", "category": "time_complexity",
                    "line": None, "description": "Nested loops detected — likely O(n²) or worse",
                    "current_complexity": "O(n²)", "optimized_complexity": "O(n)",
                    "fix": "Consider using hash maps, sorting + binary search, or set operations."})
                break
        elif not line.strip() or line.strip() == "}":
            loop_depth = max(0, loop_depth - 1)

    # String concat in loop
    if re.search(r'for\s+.*:.*\n.*\+=\s*["\']', code, re.DOTALL):
        issues.append({"severity": "medium", "category": "inefficient_loop",
            "line": None, "description": "String concatenation inside loop is O(n²)",
            "current_complexity": "O(n²)", "optimized_complexity": "O(n)",
            "fix": "Use a list and ''.join(parts) after the loop."})

    # sleep/blocking in async context
    if re.search(r'async\s+def', code) and re.search(r'time\.sleep', code):
        issues.append({"severity": "high", "category": "blocking",
            "line": None, "description": "Blocking time.sleep() inside async function",
            "current_complexity": "blocks event loop", "optimized_complexity": "non-blocking",
            "fix": "Use 'await asyncio.sleep()' instead of 'time.sleep()'."})

    return issues
