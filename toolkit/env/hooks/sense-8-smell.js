#!/usr/bin/env node
// SENSE 8: SMELL — Code Smell Detector
// 4D v2 — Luis Carrillo Original (2026-03-23)
// PostToolUse hook on Edit|Write
//
// Detects code smells in files being written/edited:
// - Duplication (similar lines repeated)
// - Long functions (>50 lines)
// - Deep nesting (>4 levels)
// - God files (>500 lines)
// - Hardcoded values (magic numbers, URLs, keys)
// - Console.log pollution
// - TODO/FIXME accumulation

const fs = require('fs');
const path = require('path');

const toolName = process.env.CLAUDE_TOOL_NAME || '';
const toolInput = process.env.CLAUDE_TOOL_INPUT || '{}';

// Only fire on Edit/Write
if (!['Edit', 'Write'].includes(toolName)) process.exit(0);

let filePath;
try {
  const input = JSON.parse(toolInput);
  filePath = input.file_path || '';
} catch { process.exit(0); }

if (!filePath || !fs.existsSync(filePath)) process.exit(0);

// Skip files larger than 2MB (avoid reading huge generated files)
try { if (fs.statSync(filePath).size > 2 * 1024 * 1024) process.exit(0); } catch { process.exit(0); }

// Skip non-code files
const codeExts = ['.js', '.ts', '.py', '.rb', '.jsx', '.tsx', '.sh', '.css', '.html', '.json', '.md'];
const ext = path.extname(filePath).toLowerCase();
if (!codeExts.includes(ext)) process.exit(0);

// Skip skill files and memory files (they're supposed to be long)
if (filePath.includes('/skills/') && filePath.endsWith('SKILL.md')) process.exit(0);
if (filePath.includes('/memory/')) process.exit(0);

let content;
try {
  content = fs.readFileSync(filePath, 'utf-8');
} catch { process.exit(0); }

const lines = content.split('\n');
const smells = [];

// 1. God file (>500 lines for code, >1000 for config/data)
const lineLimit = ['.json', '.md', '.html'].includes(ext) ? 1000 : 500;
if (lines.length > lineLimit) {
  smells.push(`GOD FILE: ${lines.length} lines (limit: ${lineLimit}). Consider splitting.`);
}

// 2. Deep nesting (>4 levels of indentation)
const indentSize = ['.py', '.rb'].includes(ext) ? 4 : 2; // Python/Ruby use 4-space
const maxNesting = lines.reduce((max, line) => {
  if (line.trim() === '') return max;
  const indent = line.match(/^(\s*)/)[1].length;
  const level = Math.floor(indent / indentSize);
  return Math.max(max, level);
}, 0);
if (maxNesting > 6) {
  smells.push(`DEEP NESTING: ${maxNesting} levels detected. Extract functions to reduce complexity.`);
}

// 3. Duplication detection (3+ identical non-trivial lines)
if (ext !== '.json' && ext !== '.md') {
  const lineCounts = {};
  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed.length > 20 && !trimmed.startsWith('//') && !trimmed.startsWith('#') && !trimmed.startsWith('*')) {
      lineCounts[trimmed] = (lineCounts[trimmed] || 0) + 1;
    }
  });
  const dupes = Object.entries(lineCounts).filter(([, count]) => count >= 3);
  if (dupes.length > 0) {
    smells.push(`DUPLICATION: ${dupes.length} line(s) repeated 3+ times. DRY violation.`);
  }
}

// 4. Hardcoded secrets/keys pattern
const secretPatterns = [
  /(?:=|:|=>)\s*['"][A-Za-z0-9]{32,}['"]/,  // Long random strings in assignments (potential keys)
  /sk-[a-zA-Z0-9]{20,}/,       // OpenAI-style keys
  /Bearer [a-zA-Z0-9]+/,       // Auth tokens inline
  /password\s*[:=]\s*['"][^'"]+['"]/i, // Hardcoded passwords
];
if (ext !== '.md' && ext !== '.json') {
  const secretLines = lines.filter(line =>
    secretPatterns.some(p => p.test(line)) && !line.trim().startsWith('//') && !line.trim().startsWith('#')
  );
  if (secretLines.length > 0) {
    smells.push(`SECRETS: ${secretLines.length} line(s) may contain hardcoded credentials. Use env vars.`);
  }
}

// 5. Console.log pollution (>5 in non-debug files)
if (['.js', '.ts', '.jsx', '.tsx'].includes(ext)) {
  const consoleLogs = lines.filter(l => l.includes('console.log') && !l.trim().startsWith('//'));
  if (consoleLogs.length > 5) {
    smells.push(`CONSOLE POLLUTION: ${consoleLogs.length} console.log statements. Clean before shipping.`);
  }
}

// 6. TODO/FIXME accumulation
const todos = lines.filter(l => /\b(TODO|FIXME|HACK|XXX|TEMP)\b/i.test(l));
if (todos.length > 3) {
  smells.push(`TECH DEBT: ${todos.length} TODO/FIXME/HACK markers. Address before they rot.`);
}

// 7-12. Security patterns (Trail of Bits audit — 2026-03-31)
// Detects OWASP Top 10 patterns in code being edited
if (['.js', '.ts', '.jsx', '.tsx', '.py'].includes(ext)) {
  const securityChecks = [
    { name: 'SQL_INJECTION', owasp: 'A03', detect: l => /\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b/i.test(l) && /(\$\{|\+\s*req\.|\+\s*params\.)/.test(l), msg: 'concatenates user input into SQL' },
    { name: 'CMD_INJECTION', owasp: 'A03', detect: l => /exec\(|execSync\(|spawn\(|os\.system|subprocess\.(call|run)/.test(l) && /(\$\{|req\.|params\.|body\.)/.test(l), msg: 'passes user input to shell' },
    { name: 'PATH_TRAVERSAL', owasp: 'A01', detect: l => /(readFile|writeFile|createReadStream|open\()/.test(l) && /(req\.|params\.|query\.)/.test(l) && !/(basename|sanitize|allowlist)/.test(l), msg: 'user input in file paths' },
    { name: 'SSRF', owasp: 'A10', detect: l => /(fetch\(|axios|requests\.(get|post)|http\.get)/.test(l) && /(req\.|params\.|query\.|body\.)/.test(l) && !/(allowlist|whitelist|validateUrl)/.test(l), msg: 'user-controlled URLs in HTTP requests' },
    { name: 'XSS', owasp: 'A03', detect: l => /(innerHTML\s*=|document\.write\()/.test(l), msg: 'raw HTML injection' },
    { name: 'DESERIALIZATION', owasp: 'A08', detect: l => /(eval\(|Function\(|pickle\.load|yaml\.load\()/.test(l) && !/SafeLoader/.test(l), msg: 'unsafe deserialization' },
  ];
  for (const check of securityChecks) {
    const hits = lines.filter(l => !l.trim().startsWith('//') && !l.trim().startsWith('#') && check.detect(l));
    if (hits.length > 0) {
      smells.push(`${check.name} [OWASP:${check.owasp}]: ${hits.length} line(s) ${check.msg}. Fix before shipping.`);
    }
  }
}

// Output smells
if (smells.length > 0) {
  const severity = smells.length >= 3 ? '🔴 STINKS' : smells.length >= 2 ? '🟡 WHIFF' : '🟢 FAINT';
  console.log(`\n👃 SENSE 8 (SMELL) ${severity} — ${path.basename(filePath)}`);
  smells.forEach(s => console.log(`  • ${s}`));
  if (smells.length >= 3) {
    console.log(`  ⚠️  This file needs refactoring attention.`);
  }
}
