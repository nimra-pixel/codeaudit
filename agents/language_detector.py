"""Language detector — detects programming language from code."""
import re
from agents.state import CodeAuditState

LANGUAGE_PATTERNS = {
    "python":     [r'^\s*def ', r'import ', r'print\(', r':\s*$', r'\.py$'],
    "javascript": [r'const |let |var ', r'=>', r'console\.log', r'\.js$', r'function\s*\('],
    "typescript": [r':\s*string|:\s*number|:\s*boolean', r'interface ', r'\.ts$', r'type '],
    "java":       [r'public\s+class', r'System\.out', r'\.java$', r'void\s+main'],
    "cpp":        [r'#include', r'std::', r'cout\s*<<', r'\.cpp$|\.h$', r'int\s+main'],
    "c":          [r'#include\s*<', r'printf\s*\(', r'\.c$', r'int\s+main\s*\('],
    "csharp":     [r'using System', r'Console\.Write', r'\.cs$', r'namespace '],
    "go":         [r'package main', r'fmt\.Print', r'\.go$', r'func\s+\w+\('],
    "rust":       [r'fn main\(\)', r'println!\(', r'\.rs$', r'let mut ', r'use std'],
    "php":        [r'<\?php', r'echo\s+', r'\.php$', r'\$\w+\s*='],
    "ruby":       [r'def\s+\w+', r'puts\s+', r'\.rb$', r'end$', r'require '],
    "swift":      [r'func\s+\w+', r'print\(', r'\.swift$', r'var\s+\w+\s*:'],
    "kotlin":     [r'fun\s+main', r'println\(', r'\.kt$', r'val\s+|var\s+'],
    "sql":        [r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO'],
    "bash":       [r'#!/bin/bash|#!/bin/sh', r'echo\s+', r'\.sh$', r'\$\{?\w+\}?'],
}


def detect_language(code: str, filename: str = "") -> str:
    """Detect programming language from code and filename."""
    # Check filename extension first
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".java": "java", ".cpp": "cpp", ".cc": "cpp", ".c": "c",
        ".cs": "csharp", ".go": "go", ".rs": "rust", ".php": "php",
        ".rb": "ruby", ".swift": "swift", ".kt": "kotlin",
        ".sql": "sql", ".sh": "bash",
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang

    # Pattern matching on code
    scores = {lang: 0 for lang in LANGUAGE_PATTERNS}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                scores[lang] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def language_detector_node(state: CodeAuditState) -> CodeAuditState:
    """LangGraph node: detect language and prepare state."""
    lang = detect_language(state["code"], state.get("filename", ""))
    print(f"[Detector] Language: {lang}")
    return {**state, "language": lang}
