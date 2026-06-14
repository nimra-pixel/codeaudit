"""
CodeAudit MCP Server
Run: python mcpserver/server.py
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from agents.language_detector import detect_language
from agents.security_agent import _static_security_check
from agents.ast_analyzer import ast_security_scan
from utils.config import get_settings

app = Server("codeaudit")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="audit_code", description="Full code audit",
            inputSchema={"type":"object","properties":{"code":{"type":"string"},"filename":{"type":"string","default":"code.py"}},"required":["code"]}),
        types.Tool(name="quick_security_scan", description="Security scan only",
            inputSchema={"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}),
        types.Tool(name="detect_language", description="Detect language",
            inputSchema={"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}),
        types.Tool(name="health_check", description="Server status",
            inputSchema={"type":"object","properties":{}}),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "health_check":
            result = {"status": "healthy", "version": "1.0.0"}
        elif name == "detect_language":
            result = {"language": detect_language(arguments.get("code",""), arguments.get("filename",""))}
        elif name == "quick_security_scan":
            code = arguments.get("code","")
            lang = detect_language(code, arguments.get("filename","code.py"))
            issues = _static_security_check(code) + (ast_security_scan(code) if lang=="python" else [])
            critical = sum(1 for i in issues if i.get("severity") in ("critical","high"))
            result = {"language":lang,"total_issues":len(issues),"critical_high":critical,"safe_to_deploy":critical==0,"issues":issues}
        elif name == "audit_code":
            from graph import run_audit
            state = run_audit(code=arguments.get("code",""), filename=arguments.get("filename","code.py"))
            result = {"grade":state.get("grade"),"overall_score":state.get("overall_score"),
                      "security_issues":state.get("security_issues",[]),"report":state.get("final_report","")[:2000]}
        else:
            result = {"error": f"Unknown tool: {name}"}
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    print("CodeAudit MCP Server ready")
    print("Tools: audit_code | quick_security_scan | detect_language | health_check")

    # Find NotificationOptions in whichever location this mcp version uses
    NotificationOptions = None
    for mod_path in [
        "mcp.server.lowlevel.server",
        "mcp.server",
        "mcp.shared.session",
        "mcp.types",
    ]:
        try:
            mod = __import__(mod_path, fromlist=["NotificationOptions"])
            NotificationOptions = getattr(mod, "NotificationOptions", None)
            if NotificationOptions:
                print(f"[MCP] NotificationOptions found in {mod_path}")
                break
        except Exception:
            continue

    if NotificationOptions:
        caps = app.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )
    else:
        # Fallback: build minimal capabilities manually
        caps = types.ServerCapabilities(tools=types.ToolsCapability(listChanged=False))

    async with mcp.server.stdio.stdio_server() as (read, write):
        await app.run(
            read, write,
            InitializationOptions(
                server_name="codeaudit",
                server_version="1.0.0",
                capabilities=caps,
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())