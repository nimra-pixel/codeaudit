<div align="center">

# 🔍 CodeAudit Agent

### AI-Powered Code Security, Quality & Performance Review

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-FF6B35?style=flat)](https://langchain-ai.github.io/langgraph/)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-8B5CF6?style=flat)](https://github.com/jlowin/fastmcp)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat)](https://groq.com)
[![Built by Nimra](https://img.shields.io/badge/Built%20by-Nimra%20Tariq-1A3A5C?style=flat&logo=github)](https://github.com/nimra-pixel)

**Paste any code → Get security vulnerabilities, quality issues, performance bottlenecks, auto-fix, and a graded report.**

Works as a Streamlit web app AND as an MCP server for VS Code.

</div>

---

## What it detects

| Category | Checks |
|----------|--------|
| 🔒 **Security** | OWASP Top 10 · SQL injection · XSS · hardcoded secrets · eval() · weak crypto · debug mode |
| ✨ **Quality** | SOLID violations · cyclomatic complexity · naming · DRY · magic numbers · error handling |
| ⚡ **Performance** | O(n²) loops · N+1 queries · memory leaks · blocking I/O · string concat in loops |

## Languages supported

Python · JavaScript · TypeScript · Java · C++ · C · C# · Go · Rust · PHP · Ruby · Swift · Kotlin · SQL · Bash

---

## Architecture

```
Code input (Streamlit UI or VS Code via MCP)
    ↓
LangGraph orchestrator
    ↓ (parallel)
┌──────────────┬──────────────┬──────────────┐
│ Security     │ Quality      │ Performance  │
│ Agent        │ Agent        │ Agent        │
│ OWASP Top 10 │ SOLID/Clean  │ Big-O/leaks  │
└──────────────┴──────────────┴──────────────┘
    ↓
Fix Agent (auto-generates fixed code)
    ↓
Scorer (computes grade A+ → F)
    ↓
Report (.md + .json export)
```

---

## Quick Start

```bash
git clone https://github.com/nimra-pixel/codeaudit.git
cd codeaudit
pip install -r requirements.txt
cp .env.example .env    # add GROQ_API_KEY
streamlit run app.py
```

## MCP Server (for VS Code)

```bash
python mcp/server.py
```

Then install the VS Code extension from `vscode/` folder.

Right-click any code → **CodeAudit: Audit This File**

---

## MCP Tools exposed

| Tool | Description |
|------|-------------|
| `audit_code` | Full security + quality + performance audit |
| `quick_security_scan` | Security only (faster) |
| `detect_code_language` | Detect programming language |

Works with LangGraph, CrewAI, Claude Desktop, and any MCP client.

---

## Built by

**Nimra Tariq** — AI Engineer & Assistant Professor, Superior University Lahore, Pakistan

[![GitHub](https://img.shields.io/badge/GitHub-nimra--pixel-181717?style=flat&logo=github)](https://github.com/nimra-pixel)

**Also built:** [MedAgent](https://github.com/nimra-pixel/medagent) · [DeepResearch](https://github.com/nimra-pixel/DeepResearch) · [VEMA](https://github.com/nimra-pixel/vema)

---
MIT License
