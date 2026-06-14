"""
CodeAudit Benchmark Suite - tests static analysis accuracy.
Run: python benchmark.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.security_agent import _static_security_check
from agents.quality_performance_agents import _static_performance_check
from agents.language_detector import detect_language

def run():
    print("=" * 50)
    print("CodeAudit Static Analysis Benchmark")
    print("=" * 50)

    # Language detection
    lang_tests = [
        ("import pandas\ndef f(): pass", "test.py", "python"),
        ("const x = () => {}", "app.js", "javascript"),
        ("public class A {}", "A.java", "java"),
        ("#include <iostream>", "main.cpp", "cpp"),
        ("SELECT * FROM t", "q.sql", "sql"),
        ("package main\nfunc main(){}", "main.go", "go"),
    ]
    lang_ok = 0
    print("\n-- Language detection --")
    for code, fname, expected in lang_tests:
        got = detect_language(code, fname)
        ok = got == expected
        if ok: lang_ok += 1
        print(f"  {'OK' if ok else 'FAIL'}  {fname}: {got}")

    # Security detection
    SQL_INJECT = 'cursor.execute("SELECT * FROM users WHERE name = " + name)'
    sec_tests = [
        (SQL_INJECT, "A03:2021", True),
        ('password = "admin123"', "A02:2021", True),
        ("result = eval(user_input)", "A03:2021", True),
        ("app.run(debug=True)", "A05:2021", True),
        ("hashlib.md5(password.encode())", "A02:2021", True),
        ("def add(a, b): return a + b", None, False),
    ]
    sec_ok = 0
    print("\n-- Security detection --")
    for code, owasp, should_find in sec_tests:
        issues = _static_security_check(code)
        found_ids = [i.get("owasp_id") for i in issues]
        ok = (owasp in found_ids) if should_find else (len(issues) == 0)
        if ok: sec_ok += 1
        label = f"find {owasp}" if should_find else "no false positives"
        print(f"  {'OK' if ok else 'FAIL'}  {label}: {found_ids}")

    # Performance detection
    NESTED = "for i in range(n):\n    for j in range(n):\n        x += 1"
    perf_tests = [
        (NESTED, "time_complexity", True),
        ("def f(): return 1 + 1", None, False),
    ]
    perf_ok = 0
    print("\n-- Performance detection --")
    for code, cat, should_find in perf_tests:
        issues = _static_performance_check(code)
        found = any(i.get("category") == cat for i in issues)
        ok = found if should_find else len(issues) == 0
        if ok: perf_ok += 1
        print(f"  {'OK' if ok else 'FAIL'}  {cat or 'clean code'}")

    # Results
    lr = lang_ok / len(lang_tests) * 100
    sr = sec_ok / len(sec_tests) * 100
    pr = perf_ok / len(perf_tests) * 100
    overall = (lr + sr + pr) / 3
    print(f"\n{'='*50}")
    print(f"Language detection:  {lang_ok}/{len(lang_tests)} = {lr:.0f}%")
    print(f"Security detection:  {sec_ok}/{len(sec_tests)} = {sr:.0f}%")
    print(f"Performance detect:  {perf_ok}/{len(perf_tests)} = {pr:.0f}%")
    print(f"Overall:             {overall:.0f}%")
    print("(LLM analysis adds further coverage for complex patterns)")
    return overall

if __name__ == "__main__":
    rate = run()
    sys.exit(0 if rate >= 75 else 1)


def run_ast_benchmark():
    """Test AST-based detection — catches what regex misses."""
    from agents.ast_analyzer import ast_security_scan
    print("\n-- AST Analysis (Python-specific, catches regex misses) --")
    ast_tests = [
        ("import pickle\npickle.loads(data)", "A08:2021", True, "pickle.loads"),
        ("import yaml\nyaml.load(data)", "A03:2021", True, "yaml.load no Loader"),
        ("subprocess.run(cmd, shell=True)", "A03:2021", True, "subprocess shell=True"),
        ("import os\nos.system(user_cmd)", "A03:2021", True, "os.system"),
        ("token = random.randint(0,1000)", "A02:2021", True, "insecure random"),
        ("if user_token == stored_token: pass", "A02:2021", True, "timing attack"),
        ("secret_key = 'abc123xyz'", "A02:2021", True, "hardcoded secret"),
        ("def add(a, b): return a + b", None, False, "clean code"),
    ]
    passed = 0
    for code, owasp, should_find, label in ast_tests:
        issues = ast_security_scan(code)
        found_ids = [i.get('owasp_id') for i in issues]
        ok = (owasp in found_ids) if should_find else (len(issues) == 0)
        if ok: passed += 1
        print(f"  {'OK' if ok else 'FAIL'}  {label}: {found_ids if issues else 'clean'}")
    rate = passed / len(ast_tests) * 100
    print(f"  AST detection: {passed}/{len(ast_tests)} = {rate:.0f}%")
    return rate


if __name__ == "__main__":
    rate = run()
    ast_rate = run_ast_benchmark()
    combined = (rate + ast_rate) / 2
    print(f"\nCombined (static + AST): {combined:.0f}%")
    sys.exit(0 if combined >= 90 else 1)
