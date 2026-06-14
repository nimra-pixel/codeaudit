/**
 * CodeAudit VS Code Extension
 * Connects to CodeAudit MCP server for AI-powered code review
 */
const vscode = require('vscode');
const http = require('http');

function activate(context) {
    console.log('CodeAudit Agent activated');

    const auditFile = vscode.commands.registerCommand('codeaudit.auditFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('CodeAudit: No active file to audit');
            return;
        }
        const code = editor.document.getText();
        const filename = editor.document.fileName.split(/[\\/]/).pop();
        await runAudit(code, filename, 'full');
    });

    const auditSelection = vscode.commands.registerCommand('codeaudit.auditSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('CodeAudit: No code selected');
            return;
        }
        const code = editor.document.getText(editor.selection);
        const filename = editor.document.fileName.split(/[\\/]/).pop();
        await runAudit(code, filename, 'selection');
    });

    const quickScan = vscode.commands.registerCommand('codeaudit.quickScan', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const code = editor.document.getText();
        const filename = editor.document.fileName.split(/[\\/]/).pop();
        await runAudit(code, filename, 'security');
    });

    context.subscriptions.push(auditFile, auditSelection, quickScan);
}

async function runAudit(code, filename, mode) {
    const config = vscode.workspace.getConfiguration('codeaudit');
    const serverUrl = config.get('mcpServerUrl', 'http://localhost:8765');

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `CodeAudit: Analyzing ${filename}...`,
        cancellable: false
    }, async (progress) => {
        progress.report({ increment: 20, message: 'Detecting language...' });
        try {
            const tool = mode === 'security' ? 'quick_security_scan' : 'audit_code';
            const result = await callMCPTool(serverUrl, tool, { code, filename });
            progress.report({ increment: 80, message: 'Done!' });
            showResults(result, filename, mode);
        } catch (err) {
            vscode.window.showErrorMessage(`CodeAudit failed: ${err.message}. Is the MCP server running?`);
        }
    });
}

function callMCPTool(serverUrl, tool, params) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify({ tool, params });
        const url = new URL(`${serverUrl}/tools/${tool}`);
        const options = {
            hostname: url.hostname,
            port: url.port || 8765,
            path: url.pathname,
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
        };
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch { reject(new Error('Invalid response from MCP server')); }
            });
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

function showResults(result, filename, mode) {
    const panel = vscode.window.createWebviewPanel(
        'codeaudit', `CodeAudit: ${filename}`,
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );

    const grade = result.grade || '?';
    const score = result.overall_score || result.total_issues !== undefined ? result.overall_score : '?';
    const gradeColor = grade.startsWith('A') ? '#16A34A' : grade.startsWith('B') ? '#D97706' : '#DC2626';

    const secIssues = (result.security_issues || []).map(i =>
        `<div class="issue ${i.severity}">
            <span class="badge ${i.severity}">${i.severity.toUpperCase()}</span>
            <strong>${i.owasp_id} — ${i.owasp_name}</strong>
            <p>${i.description}</p>
            <code>${i.fix}</code>
        </div>`
    ).join('');

    const qualIssues = (result.quality_issues || []).map(i =>
        `<div class="issue ${i.severity}">
            <span class="badge ${i.severity}">${i.severity.toUpperCase()}</span>
            <strong>${i.category}</strong>
            <p>${i.description}</p>
            <code>${i.suggestion}</code>
        </div>`
    ).join('');

    const perfIssues = (result.performance_issues || []).map(i =>
        `<div class="issue ${i.severity}">
            <span class="badge ${i.severity}">${i.severity.toUpperCase()}</span>
            <strong>${i.category}</strong>
            <p>${i.description}</p>
            <code>${i.fix}</code>
        </div>`
    ).join('');

    panel.webview.html = `<!DOCTYPE html><html><head><style>
        body{font-family:system-ui;padding:20px;background:#0d1117;color:#e6edf3;}
        .scores{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0;}
        .score-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center;}
        .grade{font-size:2.5rem;font-weight:700;color:${gradeColor};}
        .score-val{font-size:1.5rem;font-weight:600;}
        .score-lbl{font-size:0.75rem;color:#8b949e;text-transform:uppercase;}
        .section{margin:20px 0;}
        h2{border-bottom:1px solid #30363d;padding-bottom:8px;font-size:1rem;}
        .issue{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;margin:8px 0;border-left:3px solid #888;}
        .issue.critical{border-left-color:#f85149;}
        .issue.high{border-left-color:#d29922;}
        .issue.medium{border-left-color:#388bfd;}
        .issue.low{border-left-color:#3fb950;}
        .badge{font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;margin-right:8px;}
        .badge.critical{background:#f8514933;color:#f85149;}
        .badge.high{background:#d2992233;color:#d29922;}
        .badge.medium{background:#388bfd33;color:#388bfd;}
        .badge.low{background:#3fb95033;color:#3fb950;}
        code{display:block;background:#0d1117;padding:8px;border-radius:4px;margin-top:8px;font-size:0.85rem;white-space:pre-wrap;}
        p{margin:4px 0;font-size:0.9rem;color:#8b949e;}
        .safe{color:#3fb950;font-weight:600;}
        .unsafe{color:#f85149;font-weight:600;}
    </style></head><body>
        <h1>CodeAudit Report — ${filename}</h1>
        <div class="scores">
            <div class="score-card"><div class="grade">${grade}</div><div class="score-lbl">Grade</div></div>
            <div class="score-card"><div class="score-val">${typeof score === 'number' ? score.toFixed(0) : score}</div><div class="score-lbl">Overall</div></div>
            <div class="score-card"><div class="score-val">${result.security_score ? result.security_score.toFixed(0) : '—'}</div><div class="score-lbl">Security</div></div>
            <div class="score-card"><div class="score-val">${result.total_issues ?? (result.security_issues||[]).length + (result.quality_issues||[]).length + (result.performance_issues||[]).length}</div><div class="score-lbl">Issues</div></div>
        </div>
        ${mode === 'security' ? `<p class="${result.safe_to_deploy ? 'safe' : 'unsafe'}">${result.safe_to_deploy ? '✅ Safe to deploy' : '❌ NOT safe — fix critical issues first'}</p>` : ''}
        ${secIssues ? `<div class="section"><h2>🔒 Security Issues</h2>${secIssues}</div>` : ''}
        ${qualIssues ? `<div class="section"><h2>✨ Quality Issues</h2>${qualIssues}</div>` : ''}
        ${perfIssues ? `<div class="section"><h2>⚡ Performance Issues</h2>${perfIssues}</div>` : ''}
        ${!secIssues && !qualIssues && !perfIssues ? '<p style="color:#3fb950;font-size:1.2rem">✅ No issues found! Clean code.</p>' : ''}
    </body></html>`;
}

function deactivate() {}
module.exports = { activate, deactivate };
