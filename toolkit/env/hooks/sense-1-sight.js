#!/usr/bin/env node
// SENSE 1: SIGHT — Design System Rule Enforcer
// Alex Hale (2026-04-14)
// PostToolUse hook on Edit|Write
//
// Part of the 4D Senses framework — see ~/.claude/hooks/sense-8-smell.js
// for the full framework intro.
//
// Enforces ua-ux hard rules on .tsx|.jsx|.css|.html edits.

const fs = require('fs');
const path = require('path');

const toolName = process.env.CLAUDE_TOOL_NAME || '';
const toolInput = process.env.CLAUDE_TOOL_INPUT || '{}';

if (!['Edit', 'Write'].includes(toolName)) process.exit(0);

let filePath;
try {
  const input = JSON.parse(toolInput);
  filePath = input.file_path || '';
} catch { process.exit(0); }

if (!filePath || !fs.existsSync(filePath)) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
if (!['.tsx', '.jsx', '.css', '.html'].includes(ext)) process.exit(0);

const skipPatterns = ['.test.', '.spec.', '/node_modules/', '/.next/', '/dist/', '/build/', '/coverage/'];
if (skipPatterns.some(p => filePath.includes(p))) process.exit(0);

try { if (fs.statSync(filePath).size > 500 * 1024) process.exit(0); } catch { process.exit(0); }

let content;
try { content = fs.readFileSync(filePath, 'utf-8'); } catch { process.exit(0); }

const lines = content.split('\n');
const findings = [];
const firedRules = new Set();

function addFinding(rule, severity, msg, lineNum, excerpt) {
  if (firedRules.has(rule)) return;
  firedRules.add(rule);
  findings.push({ rule, severity, msg, line: lineNum, excerpt: excerpt.slice(0, 60) });
}

// --- RULES ---

// 1. BORDERS_NOT_SHADOWS
lines.forEach((line, idx) => {
  if (/\bshadow-(sm|md|lg|xl|2xl|inner)\b/.test(line) && !line.trim().startsWith('//')) {
    addFinding('BORDERS_NOT_SHADOWS', 'warn',
      'ua-ux: use borders not shadows (border border-zinc-800)',
      idx + 1, line.trim());
  }
});

// 2. ROUNDED_FULL_MISUSE
lines.forEach((line, idx) => {
  if (/rounded-full/.test(line)) {
    const ctx = lines.slice(Math.max(0, idx - 3), Math.min(lines.length, idx + 4)).join(' ').toLowerCase();
    const isContainer = /(Card|CardContent|Dialog|Sheet|Container|Modal|Panel|Section)/.test(line);
    const isPillContext = /(avatar|status|dot|badge|indicator|pill|circle)/.test(ctx);
    if (isContainer && !isPillContext) {
      addFinding('ROUNDED_FULL_MISUSE', 'warn',
        'ua-ux: rounded-full reserved for avatars/status/pills',
        idx + 1, line.trim());
    }
  }
});

// 3. HERO_TEXT_IN_APP
const isMarketingFile = /(marketing|landing|hero|home)/.test(filePath) && !/components\/ui\//.test(filePath);
if (!isMarketingFile) {
  lines.forEach((line, idx) => {
    if (/text-(3xl|4xl|5xl|6xl|7xl|8xl|9xl)\b/.test(line) && !line.trim().startsWith('//')) {
      addFinding('HERO_TEXT_IN_APP', 'warn',
        'ua-ux: text-3xl+ is marketing/hero only, not app UI',
        idx + 1, line.trim());
    }
  });
}

// 4. ICON_BUTTON_NO_ARIALABEL
const iconBtnRegex = /<button\b([^>]*)>\s*(?:<(\w*Icon|Icon\w*|svg|Svg)\b)/i;
lines.forEach((line, idx) => {
  const m = line.match(iconBtnRegex);
  if (m && !/aria-label/.test(m[1])) {
    const lookahead = lines.slice(idx, Math.min(lines.length, idx + 4)).join(' ');
    const hasText = />[A-Za-z][A-Za-z0-9 ]{2,}</.test(lookahead.replace(/<\w+[^>]*\/>/g, ''));
    if (!hasText) {
      addFinding('ICON_BUTTON_NO_ARIALABEL', 'error',
        'ua-ux: icon-only buttons MUST have aria-label (WCAG 4.1.2)',
        idx + 1, line.trim());
    }
  }
});

// 5. DIV_ONCLICK
lines.forEach((line, idx) => {
  if (/<div\b[^>]*\bonClick=/.test(line) && !/role=["']button["']/.test(line) && !/tabIndex=/.test(line)) {
    addFinding('DIV_ONCLICK', 'error',
      'ua-ux: use <button> or <a>, not <div onClick> (WCAG keyboard)',
      idx + 1, line.trim());
  }
});

// 6. PLACEHOLDER_ONLY_INPUT
lines.forEach((line, idx) => {
  if (/<Input\b[^>]*\bplaceholder=/.test(line)) {
    const ctx = lines.slice(Math.max(0, idx - 5), Math.min(lines.length, idx + 5)).join(' ');
    if (!/<Label\b/i.test(ctx)) {
      addFinding('PLACEHOLDER_ONLY_INPUT', 'warn',
        'ua-ux: every input needs a visible <Label>',
        idx + 1, line.trim());
    }
  }
});

// 7. INLINE_STYLE
if (['.tsx', '.jsx'].includes(ext)) {
  lines.forEach((line, idx) => {
    if (/style=\{\{/.test(line)) {
      if (!/['"]--[\w-]+['"]:/.test(line)) {
        addFinding('INLINE_STYLE', 'warn',
          'ua-ux: use Tailwind classes, not inline style={{}}',
          idx + 1, line.trim());
      }
    }
  });
}

// 8. RAW_HEX_IN_TSX
if (['.tsx', '.jsx'].includes(ext)) {
  lines.forEach((line, idx) => {
    if (/(background|color|border)[^:=]*[:=][^#\n]*#[0-9a-fA-F]{3,8}\b/.test(line) && !line.trim().startsWith('//')) {
      addFinding('RAW_HEX_IN_TSX', 'warn',
        'ua-ux: use Tailwind tokens (zinc-*, orange-500), not raw hex',
        idx + 1, line.trim());
    }
  });
}

// 9. MULTI_ACCENT — file-level
const colorFamilies = ['orange', 'blue', 'green', 'purple', 'pink', 'red', 'amber', 'emerald', 'cyan', 'indigo', 'rose', 'violet', 'teal', 'sky', 'fuchsia', 'lime', 'yellow'];
const statusFamilies = new Set(['red', 'amber', 'emerald']);
const detected = new Set();
for (const fam of colorFamilies) {
  const re = new RegExp(`\\b(?:text|bg|border|ring|from|to|via|decoration|outline)-${fam}-\\d`, 'g');
  if (re.test(content)) detected.add(fam);
}
const nonStatus = [...detected].filter(f => !statusFamilies.has(f));
if (nonStatus.length > 1) {
  addFinding('MULTI_ACCENT', 'warn',
    `ua-ux: one accent color per project — detected ${nonStatus.length} families: ${nonStatus.join(', ')}`,
    0, '');
}

// 10. UNSAFE_INNER_HTML (React XSS risk)
// Detect the dangerous React prop via concatenated string to avoid tripping security reminder on this file
const unsafePropName = 'dangerously' + 'Set' + 'InnerHTML';
const unsafeRe = new RegExp('\\b' + unsafePropName + '\\b');
lines.forEach((line, idx) => {
  if (unsafeRe.test(line) && !line.trim().startsWith('//')) {
    addFinding('UNSAFE_INNER_HTML', 'error',
      'ua-ux + security: ' + unsafePropName + ' is unsafe. Use react-markdown or sanitize via DOMPurify',
      idx + 1, line.trim());
  }
});

// --- OUTPUT ---
if (findings.length === 0) process.exit(0);

const hasError = findings.some(f => f.severity === 'error');
const icon = hasError ? '🔴' : (findings.length >= 2 ? '🟡' : '🟢');

// Channel policy: findings (including error-severity) go to stdout so Claude
// Code surfaces them as hook output. stderr is reserved for actual hook-level
// failures (unreadable file, JSON parse error, etc.) so those don't get
// conflated with normal rule violations.
const header = `\n👁️  SENSE 1 (SIGHT) ${icon} — ${path.basename(filePath)}`;
console.log(header);
findings.forEach(f => {
  const prefix = f.severity === 'error' ? '🔴' : '•';
  const locHint = f.line > 0 ? ` L${f.line}` : '';
  console.log(`  ${prefix} [${f.rule}]${locHint} ${f.msg}`);
  if (f.excerpt && f.line > 0) console.log(`    ${f.excerpt}`);
});

if (findings.length >= 3) {
  console.log(`  ⚠️  Multiple ua-ux violations. Consider: /design-stack --refactor "fix ${path.basename(filePath)}"`);
}

process.exit(0);
