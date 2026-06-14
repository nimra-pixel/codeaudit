"""
Security Agent
Detects OWASP Top 10 vulnerabilities and security issues.
"""
import re
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import CodeAuditState
from utils.config import invoke_llm
from agents.ast_analyzer import ast_security_scan

SECURITY_SYSTEM = """You are a senior application security engineer (OWASP expert).
Analyze the code for security vulnerabilities.

Return ONLY valid JSON:
{
  "issues": [
    {
      "severity": "critical | high | medium | low | info",
      "owasp_id": "A01:2021",
      "owasp_name": "Broken Access Control",
      "line": 15,
      "description": "Clear description of the vulnerability",
      "vulnerable_code": "exact code snippet",
      "fix": "Fixed code or explanation",
      "cve": null
    }
  ],
  "summary": "Overall security assessment in 1 sentence"
}

OWASP Top 10 2021 to check:
A01 - Broken Access Control
A02 - Cryptographic Failures (weak hashing, hardcoded keys, HTTP not HTTPS)
A03 - Injection (SQL injection, command injection, XSS, SSTI)
A04 - Insecure Design
A05 - Security Misconfiguration (debug=True, default creds, verbose errors)
A06 - Vulnerable Components (outdated imports)
A07 - Auth Failures (weak passwords, no rate limiting, broken session)
A08 - Software Integrity Failures
A09 - Logging Failures (logging sensitive data, no logging)
A10 - SSRF

Also check: hardcoded secrets/API keys, eval() usage, unsafe deserialization,
path traversal, XXE, insecure random, timing attacks.

Be thorough but precise. Only report real issues, not false positives.
Return ONLY JSON."""


def security_agent(state: CodeAuditState) -> CodeAuditState:
    """Detect security vulnerabilities in code."""
    code = state["code"]
    lang = state.get("language", "unknown")

    # Quick static checks first (no LLM needed)
    static_issues = _static_security_check(code)

    # LLM deep analysis
    prompt = f"Language: {lang}\n\nCode to audit:\n```{lang}\n{code[:3000]}\n```"
    try:
        raw = invoke_llm(
            [SystemMessage(content=SECURITY_SYSTEM), HumanMessage(content=prompt)],
            temperature=0.0, max_tokens=2048,
        )
        raw = re.sub(r'```(?:json)?|```', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group() if match else raw)
        llm_issues = result.get("issues", [])
    except Exception as e:
        print(f"[Security] LLM error: {e}")
        llm_issues = []

    # AST analysis (Python only — catches what regex misses)
    ast_issues = []
    if lang == "python":
        ast_issues = ast_security_scan(code)
        print(f"[Security] AST: {len(ast_issues)} additional issues found")

    # Merge static + AST + LLM issues, deduplicate
    all_issues = static_issues + ast_issues + llm_issues
    seen, unique = set(), []
    for issue in all_issues:
        key = issue.get("owasp_id", "") + issue.get("description", "")[:40]
        if key not in seen:
            seen.add(key)
            unique.append(issue)

    # Sort by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    unique.sort(key=lambda x: sev_order.get(x.get("severity", "info"), 4))

    print(f"[Security] Found {len(unique)} issues ({len(static_issues)} regex + {len(ast_issues)} AST + {len(llm_issues)} LLM)")
    return {**state, "security_issues": unique}


def _static_security_check(code: str) -> list:
    """Fast regex-based security checks — no LLM needed."""
    issues = []

    # Hardcoded secrets
    secret_patterns = [
        (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
        (r'(?i)(api_key|apikey|secret_key|token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key/secret"),
        (r'(?i)(aws_access|aws_secret)', "Potential AWS credentials in code"),
    ]
    for pattern, desc in secret_patterns:
        if re.search(pattern, code):
            issues.append({
                "severity": "critical",
                "owasp_id": "A02:2021",
                "owasp_name": "Cryptographic Failures",
                "line": None,
                "description": desc,
                "vulnerable_code": "",
                "fix": "Use environment variables or a secrets manager. Never hardcode credentials.",
                "cve": None,
            })

    # SQL injection patterns
    sql_patterns = [
        r'execute\s*\(\s*["\']+.*%s',
        r'cursor\.execute\s*\(\s*f["\']+',
        r'cursor\.execute\s*\([^)]*\+',
        r'query\s*=\s*f["\']+.*SELECT',
    ]
    for pattern in sql_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                "severity": "critical",
                "owasp_id": "A03:2021",
                "owasp_name": "Injection",
                "line": None,
                "description": "Potential SQL injection via string formatting",
                "vulnerable_code": "",
                "fix": "Use parameterized queries or prepared statements.",
                "cve": None,
            })
            break

    # eval() usage
    if re.search(r'\beval\s*\(', code):
        issues.append({
            "severity": "high",
            "owasp_id": "A03:2021",
            "owasp_name": "Injection",
            "line": None,
            "description": "eval() usage can execute arbitrary code",
            "vulnerable_code": "eval(...)",
            "fix": "Avoid eval(). Use ast.literal_eval() for data, or restructure the logic.",
            "cve": None,
        })

    # Debug mode
    if re.search(r'debug\s*=\s*True', code, re.IGNORECASE):
        issues.append({
            "severity": "medium",
            "owasp_id": "A05:2021",
            "owasp_name": "Security Misconfiguration",
            "line": None,
            "description": "Debug mode enabled — exposes stack traces and sensitive info",
            "vulnerable_code": "debug=True",
            "fix": "Set debug=False in production. Use environment variables.",
            "cve": None,
        })

    # MD5/SHA1 for passwords
    if re.search(r'md5|sha1', code, re.IGNORECASE) and re.search(r'password|passwd', code, re.IGNORECASE):
        issues.append({
            "severity": "high",
            "owasp_id": "A02:2021",
            "owasp_name": "Cryptographic Failures",
            "line": None,
            "description": "MD5/SHA1 used for password hashing — these are cryptographically broken",
            "vulnerable_code": "",
            "fix": "Use bcrypt, argon2, or PBKDF2 for password hashing.",
            "cve": "CVE-2004-2761",
        })

    return issues
