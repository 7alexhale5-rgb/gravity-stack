#!/usr/bin/env node
// SENSE 10: PAIN — Automatic Damage Detection & Reflex
// 4D v2 — Luis Carrillo Original (2026-03-23)
// PostToolUse hook on Edit|Write|Bash
//
// Pain reflex system:
// 1. Before risky edits → git stash create (auto-checkpoint)
// 2. After tool failure → flag the pain
// 3. Tracks accumulated pain in session (repeated failures = escalate)
// 4. Auto-rollback suggestion when tests fail after edit

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const toolName = process.env.CLAUDE_TOOL_NAME || '';
const toolInput = process.env.CLAUDE_TOOL_INPUT || '{}';
const toolResult = process.env.CLAUDE_TOOL_RESULT || '';
const PAIN_LOG = path.join(process.env.HOME, '.claude/sensory-memory/pain-log.json');

// Load pain history
let painHistory = [];
try {
  if (fs.existsSync(PAIN_LOG)) {
    painHistory = JSON.parse(fs.readFileSync(PAIN_LOG, 'utf-8'));
    // Keep only last 50 entries
    if (painHistory.length > 50) painHistory = painHistory.slice(-50);
  }
} catch { painHistory = []; }

function logPain(type, detail, severity) {
  const entry = {
    time: new Date().toISOString(),
    type,
    detail: detail.substring(0, 200),
    severity, // 1-5
    tool: toolName
  };
  painHistory.push(entry);
  fs.writeFileSync(PAIN_LOG, JSON.stringify(painHistory, null, 2));
  return entry;
}

// --- PAIN DETECTION ---

// 1. Bash command failures (exit code != 0)
if (toolName === 'Bash') {
  const resultLower = (toolResult || '').toLowerCase();
  const failurePatterns = [
    { pattern: /segmentation fault/i, type: 'SEGFAULT', severity: 5 },
    { pattern: /killed|oom/i, type: 'OOM_KILL', severity: 5 },
    { pattern: /syntax error/i, type: 'SYNTAX_ERROR', severity: 4 },
    { pattern: /traceback|exception/i, type: 'EXCEPTION', severity: 3 },
    { pattern: /FAIL|FAILED/i, type: 'TEST_FAILURE', severity: 3 },
    { pattern: /permission denied/i, type: 'PERMISSION_DENIED', severity: 3 },
    { pattern: /not found/i, type: 'NOT_FOUND', severity: 2 },
    { pattern: /error:/i, type: 'COMMAND_ERROR', severity: 2 },
  ];

  for (const { pattern, type, severity } of failurePatterns) {
    if (pattern.test(resultLower)) {
      const pain = logPain(type, toolResult.substring(0, 200), severity);

      // Check for repeated pain (same type in last 5 min)
      const recentSame = painHistory.filter(p =>
        p.type === type &&
        (new Date() - new Date(p.time)) < 5 * 60 * 1000
      );

      if (recentSame.length >= 3) {
        console.log(`\n🔴 SENSE 10 (PAIN) — REPEATED PAIN DETECTED!`);
        console.log(`   ${type} happened ${recentSame.length}x in 5 minutes.`);
        console.log(`   STOP. Step back. Diagnose root cause before retrying.`);
        console.log(`   "3 errors in a row = wrong approach, not bad luck."`);
      } else if (severity >= 4) {
        console.log(`\n🟡 SENSE 10 (PAIN) — Sharp pain: ${type}`);
        console.log(`   Consider reverting last change. Check git stash list.`);
      }
      break;
    }
  }
}

// 2. Edit/Write to critical files → checkpoint reminder
if (['Edit', 'Write'].includes(toolName)) {
  let filePath;
  try {
    filePath = JSON.parse(toolInput).file_path || '';
  } catch { filePath = ''; }

  const criticalPaths = [
    'settings.json', 'CLAUDE.md', 'package.json', 'requirements.txt',
    'Gemfile', 'deploy', '.env', 'config', 'migration'
  ];

  const isCritical = criticalPaths.some(p => filePath.includes(p));

  if (isCritical) {
    // Log critical file edit (git stash removed — was blocking + not recoverable)
    try {
      fs.appendFileSync(path.join(process.env.HOME, '.claude/sensory-memory/pain-checkpoints.log'),
        `${new Date().toISOString()} | CRITICAL_EDIT | ${filePath}\n`
      );
    } catch { /* sensory-memory dir may not exist yet */ }
  }
}

// 3. Session pain summary (if high accumulated pain)
const sessionPain = painHistory.filter(p =>
  (new Date() - new Date(p.time)) < 30 * 60 * 1000
);
const totalSeverity = sessionPain.reduce((sum, p) => sum + p.severity, 0);

if (totalSeverity >= 15 && sessionPain.length >= 5) {
  // Only show this once per session (debounce)
  const debounceFile = path.join(process.env.HOME, '.claude/sensory-memory/pain-session-alert');
  const lastAlert = fs.existsSync(debounceFile) ?
    fs.readFileSync(debounceFile, 'utf-8') : '0';

  if (Date.now() - parseInt(lastAlert) > 10 * 60 * 1000) { // 10 min debounce
    console.log(`\n🔴 SENSE 10 (PAIN) — SESSION PAIN ACCUMULATING`);
    console.log(`   ${sessionPain.length} pain events (severity: ${totalSeverity}) in last 30 min`);
    console.log(`   Top types: ${[...new Set(sessionPain.map(p => p.type))].join(', ')}`);
    console.log(`   Consider: pause, review approach, or ask for help.`);
    fs.writeFileSync(debounceFile, Date.now().toString());
  }
}
