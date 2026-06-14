"""CodeAudit Agent — AI-Powered Code Review"""
import streamlit as st
import uuid, json, os, time, threading
from datetime import datetime

st.set_page_config(page_title="CodeAudit Agent", page_icon="🔍",
                   layout="wide", initial_sidebar_state="collapsed")

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:8]
if "result" not in st.session_state:
    st.session_state.result = None
if "run_count" not in st.session_state:
    st.session_state.run_count = 0

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0D1117;}
[data-testid="collapsedControl"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}

.topnav{background:#161B22;border:1px solid #30363D;border-radius:12px;padding:1rem 1.5rem;display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;}
.topnav-title{font-size:1.4rem;font-weight:700;color:#E6EDF3;margin:0;}
.topnav-sub{color:#8B949E;font-size:0.78rem;margin-top:2px;}
.nbadge{background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#A78BFA;border-radius:20px;padding:0.18rem 0.65rem;font-size:0.7rem;font-weight:500;}

.card{background:#161B22;border:1px solid #30363D;border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:0.8rem;}
.card-title{font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#8B949E;margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid #30363D;}

.stTextArea textarea{background:#0D1117!important;border:1px solid #30363D!important;border-radius:8px!important;color:#E6EDF3!important;font-family:'JetBrains Mono',monospace!important;font-size:0.85rem!important;}
.stTextArea textarea:focus{border-color:#388BFD!important;}
.stTextInput input,.stSelectbox>div>div{background:#161B22!important;border:1px solid #30363D!important;border-radius:8px!important;color:#E6EDF3!important;}
label{font-size:0.72rem!important;font-weight:600!important;color:#8B949E!important;text-transform:uppercase!important;letter-spacing:0.05em!important;}
.stButton>button{background:#21262D!important;color:#E6EDF3!important;border:1px solid #30363D!important;border-radius:8px!important;font-weight:600!important;}
.stButton>button:hover{background:#388BFD!important;border-color:#388BFD!important;}

.score-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:1rem;}
.score-card{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:1rem;text-align:center;}
.grade-val{font-size:2rem;font-weight:700;line-height:1;}
.score-val{font-size:1.4rem;font-weight:600;color:#E6EDF3;}
.score-lbl{font-size:0.65rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.06em;margin-top:4px;}

.issue-card{background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:0.9rem 1rem;margin-bottom:0.5rem;}
.issue-critical{border-left:3px solid #F85149;}
.issue-high{border-left:3px solid #D29922;}
.issue-medium{border-left:3px solid #388BFD;}
.issue-low{border-left:3px solid #3FB950;}
.badge{display:inline-block;font-size:0.65rem;font-weight:700;padding:2px 7px;border-radius:4px;margin-right:6px;}
.badge-critical{background:#F8514933;color:#F85149;}
.badge-high{background:#D2992233;color:#D29922;}
.badge-medium{background:#388BFD33;color:#388BFD;}
.badge-low{background:#3FB95033;color:#3FB950;}

.report-box{background:#0D1117;border:1px solid #30363D;border-radius:10px;padding:1.5rem;font-family:'JetBrains Mono',monospace;font-size:0.82rem;white-space:pre-wrap;color:#E6EDF3;overflow:auto;}
.fixed-code{background:#0D1117;border:1px solid #3FB95033;border-left:3px solid #3FB950;border-radius:8px;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:0.82rem;white-space:pre-wrap;color:#E6EDF3;overflow:auto;}

.stTabs [data-baseweb="tab-list"]{background:#161B22;border-radius:8px;padding:3px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:6px;font-weight:500;font-size:0.85rem;color:#8B949E;}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#E6EDF3!important;font-weight:600!important;}

.lang-badge{display:inline-block;background:#21262D;border:1px solid #30363D;border-radius:6px;padding:3px 10px;font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#A78BFA;margin-bottom:0.5rem;}
.safe-deploy{background:#3FB95015;border:1px solid #3FB95033;border-radius:8px;padding:0.7rem 1rem;color:#3FB950;font-weight:500;}
.unsafe-deploy{background:#F8514915;border:1px solid #F8514933;border-radius:8px;padding:0.7rem 1rem;color:#F85149;font-weight:500;}
</style>
""", unsafe_allow_html=True)

# Top nav
st.markdown("""
<div class="topnav">
  <div>
    <div class="topnav-title">🔍 CodeAudit Agent</div>
    <div class="topnav-sub">AI Security · Quality · Performance · LangGraph + MCP</div>
  </div>
  <div style="display:flex;gap:0.4rem;flex-wrap:wrap">
    <span class="nbadge">🔒 OWASP Top 10</span>
    <span class="nbadge">✨ Clean Code</span>
    <span class="nbadge">⚡ Performance</span>
    <span class="nbadge">🔧 Auto-Fix</span>
    <span class="nbadge">🔌 MCP Server</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Input area
col_code, col_cfg = st.columns([3, 1])

with col_code:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📝 Code Input</div>', unsafe_allow_html=True)
    code_input = st.text_area(
        "Paste your code here",
        placeholder="# Paste any code here — Python, JS, Java, C++, Go, Rust, PHP, Ruby...\n\nimport sqlite3\n\ndef get_user(username):\n    conn = sqlite3.connect('users.db')\n    cursor = conn.cursor()\n    query = f\"SELECT * FROM users WHERE name = '{username}'\"\n    cursor.execute(query)\n    return cursor.fetchall()",
        height=320, label_visibility="collapsed",
    )
    filename = st.text_input("Filename (optional)", placeholder="main.py, index.js, App.java ...",
                              label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

with col_cfg:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">⚙️ Options</div>', unsafe_allow_html=True)
    run_fix = st.toggle("🔧 Auto-fix code", value=True, help="Generate fixed version of the code")
    run_quick = st.toggle("⚡ Quick scan only", value=False, help="Security only — faster")
    st.markdown('</div>', unsafe_allow_html=True)

    # MCP Server status
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔌 MCP Server</div>', unsafe_allow_html=True)
    import socket
    def check_mcp():
        try:
            s = socket.create_connection(("localhost", 8765), timeout=1)
            s.close()
            return True
        except Exception:
            return False
    mcp_running = check_mcp()
    if mcp_running:
        st.markdown('<div style="color:#3FB950;font-size:0.82rem">● Connected · localhost:8765</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#8B949E;font-size:0.82rem">○ Not running</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#8B949E;font-size:0.75rem;margin-top:4px">Run: python mcp/server.py</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Sample code buttons
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🧪 Try samples</div>', unsafe_allow_html=True)
    if st.button("Python SQL injection", use_container_width=True):
        st.session_state._sample = "python_sql"
    if st.button("JS XSS vulnerability", use_container_width=True):
        st.session_state._sample = "js_xss"
    if st.button("Clean Python code", use_container_width=True):
        st.session_state._sample = "python_clean"
    st.markdown('</div>', unsafe_allow_html=True)

# Handle samples
SAMPLES = {
    "python_sql": (
        "vulnerable.py",
        '''import sqlite3\nimport hashlib\n\npassword = "admin123"\ndebug = True\n\ndef get_user(username):\n    conn = sqlite3.connect("users.db")\n    cursor = conn.cursor()\n    query = f"SELECT * FROM users WHERE name = \'{username}\'"\n    cursor.execute(query)\n    return cursor.fetchall()\n\ndef check_password(pwd):\n    return hashlib.md5(pwd.encode()).hexdigest()\n\ndef process_data(data):\n    return eval(data)\n'''
    ),
    "js_xss": (
        "app.js",
        '''const express = require("express");\nconst app = express();\n\napp.get("/search", (req, res) => {\n    const query = req.query.q;\n    res.send(`<h1>Results for: ${query}</h1>`);\n});\n\napp.post("/login", (req, res) => {\n    const { username, password } = req.body;\n    const query = `SELECT * FROM users WHERE username = \'${username}\' AND password = \'${password}\'`;\n    db.query(query, (err, result) => {\n        if (result.length > 0) res.json({ token: "hardcoded_secret_key_123" });\n    });\n});\n'''
    ),
    "python_clean": (
        "calculator.py",
        '''def calculate_bmi(weight_kg: float, height_m: float) -> dict:\n    """Calculate BMI and return category."""\n    if height_m <= 0 or weight_kg <= 0:\n        raise ValueError("Weight and height must be positive")\n    bmi = weight_kg / (height_m ** 2)\n    if bmi < 18.5:\n        category = "Underweight"\n    elif bmi < 25:\n        category = "Normal"\n    elif bmi < 30:\n        category = "Overweight"\n    else:\n        category = "Obese"\n    return {"bmi": round(bmi, 2), "category": category}\n'''
    ),
}

sample_key = st.session_state.pop("_sample", None)
if sample_key and sample_key in SAMPLES:
    fname, scode = SAMPLES[sample_key]
    filename = fname
    code_input = scode

# Run button
run_col, clear_col = st.columns([6, 1])
with run_col:
    run_btn = st.button("🔍 Run Audit", type="primary", use_container_width=True)
with clear_col:
    if st.button("🗑️", use_container_width=True):
        st.session_state.result = None
        st.rerun()

# Execute
if run_btn:
    if not code_input.strip():
        st.warning("⚠️ Please paste some code to audit.")
    else:
        result_holder, error_holder = {}, {}
        _sid = st.session_state.session_id

        def _run():
            try:
                from graph import run_audit
                result_holder["state"] = run_audit(
                    code=code_input,
                    filename=filename or "code.py",
                    session_id=_sid,
                )
            except Exception as e:
                import traceback
                error_holder["err"] = e
                error_holder["tb"] = traceback.format_exc()

        steps = [
            (15, "🔍 Detecting language..."),
            (35, "🔒 Scanning security vulnerabilities..."),
            (55, "✨ Analyzing code quality..."),
            (75, "⚡ Checking performance..."),
            (88, "🔧 Generating fixes..."),
            (95, "📊 Computing scores..."),
        ]
        progress = st.progress(0, text="🚀 Starting audit...")
        t = threading.Thread(target=_run)
        t.start()
        for pct, msg in steps:
            time.sleep(1.2)
            if not t.is_alive(): break
            progress.progress(pct, text=msg)
        t.join(timeout=120)
        progress.progress(100, text="✅ Audit complete!")
        time.sleep(0.3)
        progress.empty()

        if error_holder:
            err_str = str(error_holder["err"])
            if "429" in err_str or "rate_limit" in err_str.lower():
                st.error("⏱️ Groq rate limit — wait ~20 minutes or use a new API key")
            else:
                st.error(f"Error: {error_holder['err']}")
                st.code(error_holder.get("tb", ""))
        else:
            st.session_state.result = result_holder["state"]
            st.session_state.run_count += 1
            st.rerun()

# Results
if st.session_state.result:
    state = st.session_state.result
    grade = state.get("grade", "?")
    overall = state.get("overall_score", 0)
    sec_score = state.get("security_score", 0)
    qual_score = state.get("quality_score", 0)
    perf_score = state.get("performance_score", 0)
    sec_issues = state.get("security_issues", [])
    qual_issues = state.get("quality_issues", [])
    perf_issues = state.get("performance_issues", [])
    lang = state.get("language", "?")
    total = len(sec_issues) + len(qual_issues) + len(perf_issues)
    critical_count = sum(1 for i in sec_issues if i.get("severity") in ("critical","high"))

    grade_color = "#3FB950" if grade.startswith("A") else "#D29922" if grade.startswith("B") else "#F85149"
    sec_color = "#3FB950" if sec_score >= 80 else "#D29922" if sec_score >= 60 else "#F85149"
    safe_deploy = critical_count == 0

    # Language badge
    st.markdown(f'<div class="lang-badge">⚡ {lang.upper()}</div>', unsafe_allow_html=True)

    # Deploy safety
    if safe_deploy:
        st.markdown('<div class="safe-deploy">✅ Safe to deploy — no critical security issues</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="unsafe-deploy">❌ NOT safe to deploy — {critical_count} critical/high security issue(s) must be fixed first</div>', unsafe_allow_html=True)

    # Score grid
    st.markdown(f"""
    <div class="score-grid">
      <div class="score-card"><div class="grade-val" style="color:{grade_color}">{grade}</div><div class="score-lbl">Grade</div></div>
      <div class="score-card"><div class="score-val">{overall:.0f}</div><div class="score-lbl">Overall /100</div></div>
      <div class="score-card"><div class="score-val" style="color:{sec_color}">{sec_score:.0f}</div><div class="score-lbl">Security</div></div>
      <div class="score-card"><div class="score-val">{qual_score:.0f}</div><div class="score-lbl">Quality</div></div>
      <div class="score-card"><div class="score-val">{perf_score:.0f}</div><div class="score-lbl">Performance</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tabs = st.tabs(["🔒 Security", "✨ Quality", "⚡ Performance", "🔧 Fixed Code", "📋 Report", "📥 Export"])

    def render_issue(issue, kind):
        sev = issue.get("severity","low")
        badge_map = {"critical":"badge-critical","high":"badge-high","medium":"badge-medium","low":"badge-low"}
        badge = badge_map.get(sev,"badge-low")
        if kind == "security":
            title = f"{issue.get('owasp_id','')} — {issue.get('owasp_name','')}"
            detail = f"<p style='color:#8B949E;font-size:0.85rem;margin:4px 0'>{issue.get('description','')}</p>"
            fix = f"<code style='display:block;background:#0D1117;padding:8px;border-radius:4px;margin-top:6px;font-family:monospace;font-size:0.8rem;color:#3FB950'>{issue.get('fix','')}</code>"
            cve = f"<span style='font-size:0.72rem;color:#8B949E'>CVE: {issue['cve']}</span>" if issue.get('cve') else ""
        elif kind == "quality":
            title = issue.get("category","").replace("_"," ").title()
            detail = f"<p style='color:#8B949E;font-size:0.85rem;margin:4px 0'>{issue.get('description','')}</p>"
            fix = f"<code style='display:block;background:#0D1117;padding:8px;border-radius:4px;margin-top:6px;font-family:monospace;font-size:0.8rem;color:#388BFD'>{issue.get('suggestion','')}</code>"
            cve = ""
        else:
            title = issue.get("category","").replace("_"," ").title()
            comp = f" · {issue.get('current_complexity','')} → {issue.get('optimized_complexity','')}" if issue.get('current_complexity') else ""
            detail = f"<p style='color:#8B949E;font-size:0.85rem;margin:4px 0'>{issue.get('description','')}{comp}</p>"
            fix = f"<code style='display:block;background:#0D1117;padding:8px;border-radius:4px;margin-top:6px;font-family:monospace;font-size:0.8rem;color:#D29922'>{issue.get('fix','')}</code>"
            cve = ""
        line_info = f" · Line {issue['line']}" if issue.get('line') else ""
        return f'<div class="issue-card issue-{sev}"><span class="badge {badge}">{sev.upper()}</span><strong style="color:#E6EDF3;font-size:0.9rem">{title}</strong><span style="color:#8B949E;font-size:0.78rem">{line_info}</span>{detail}{fix}{cve}</div>'

    with tabs[0]:
        if sec_issues:
            st.markdown(f"**{len(sec_issues)} security issue(s) found**")
            for i in sec_issues:
                st.markdown(render_issue(i, "security"), unsafe_allow_html=True)
        else:
            st.success("✅ No security vulnerabilities detected!")

    with tabs[1]:
        if qual_issues:
            st.markdown(f"**{len(qual_issues)} quality issue(s) found**")
            for i in qual_issues:
                st.markdown(render_issue(i, "quality"), unsafe_allow_html=True)
        else:
            st.success("✅ Code quality is excellent!")

    with tabs[2]:
        if perf_issues:
            st.markdown(f"**{len(perf_issues)} performance issue(s) found**")
            for i in perf_issues:
                st.markdown(render_issue(i, "performance"), unsafe_allow_html=True)
        else:
            st.success("✅ No performance issues detected!")

    with tabs[3]:
        fixed = state.get("fixed_code","")
        diff = state.get("diff_summary","")
        original = state.get("code","")

        if diff:
            st.markdown("**Changes / Fix guide:**")
            for line in diff.split("\n"):
                if line.strip():
                    st.markdown(f"{line.strip()}")
            st.markdown("---")

        if fixed and fixed != original:
            st.markdown("**Fixed code:**")
            st.markdown('<div class="fixed-code">' + fixed.replace('<','&lt;').replace('>','&gt;') + '</div>', unsafe_allow_html=True)
            st.download_button("📥 Download fixed code", data=fixed,
                file_name=f"fixed_{state.get('filename','code.py')}",
                mime="text/plain", use_container_width=True)
        elif not diff:
            st.info("No fixes applied — code is already clean or auto-fix was disabled.")

    with tabs[4]:
        report = state.get("final_report","")
        if report:
            st.markdown(report)
        else:
            st.info("No report generated.")

    with tabs[5]:
        col1, col2 = st.columns(2)
        with col1:
            report_text = state.get("final_report","")
            st.download_button("📥 Download .md report", data=report_text,
                file_name=f"codeaudit_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown", use_container_width=True)
        with col2:
            rj = state.get("report_json",{})
            st.download_button("📥 Download JSON report", data=json.dumps(rj, indent=2, default=str),
                file_name=f"codeaudit_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json", use_container_width=True)
        if st.button("🔄 New Audit", use_container_width=True):
            st.session_state.result = None
            st.rerun()

elif not run_btn:
    st.markdown("""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:2.5rem 2rem;text-align:center;margin-top:1rem">
      <div style="font-size:3rem;margin-bottom:0.75rem">🔍</div>
      <h3 style="color:#E6EDF3;margin:0 0 0.4rem">Ready to audit your code</h3>
      <p style="color:#8B949E;font-size:0.9rem">Paste code above and click Run Audit. Works with Python, JavaScript, Java, C++, Go, Rust, PHP, Ruby, C# and more.</p>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:1.5rem;text-align:left">
        <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:0.85rem">
          <strong style="color:#F85149;display:block;margin-bottom:3px">🔒 Security</strong>
          <span style="color:#8B949E;font-size:0.82rem">OWASP Top 10 · SQL injection · XSS · hardcoded secrets · eval() · weak crypto</span>
        </div>
        <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:0.85rem">
          <strong style="color:#388BFD;display:block;margin-bottom:3px">✨ Quality</strong>
          <span style="color:#8B949E;font-size:0.82rem">SOLID principles · cyclomatic complexity · naming · DRY violations · error handling</span>
        </div>
        <div style="background:#0D1117;border:1px solid #30363D;border-radius:8px;padding:0.85rem">
          <strong style="color:#D29922;display:block;margin-bottom:3px">⚡ Performance</strong>
          <span style="color:#8B949E;font-size:0.82rem">Big-O analysis · N+1 queries · memory leaks · blocking I/O · nested loops</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
