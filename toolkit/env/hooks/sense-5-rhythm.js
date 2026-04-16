#!/usr/bin/env node
// SENSE 5: RHYTHM — Spacing & Typography Scale Enforcer
// Alex Hale (2026-04-14)
// PostToolUse hook on Edit|Write
//
// Part of the 4D Senses framework — see ~/.claude/hooks/sense-8-smell.js
// for the full framework intro.
//
// Enforces Tailwind scale discipline on TSX/JSX/CSS:
// - Arbitrary values class-[xxx] outside marketing dirs
// - Off-scale spacing (p-13, m-15, etc.)
// - Odd gap values (prefer gap-{1,2,4,6,8})
// - Unknown text sizes (text-huge, text-bigger, etc.)
// - Arbitrary rounded-[npx] corners

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
if (!['.tsx', '.jsx', '.css', '.html', '.vue', '.svelte'].includes(ext)) process.exit(0);

const skipPatterns = ['.test.', '.spec.', '/node_modules/', '/.next/', '/dist/', '/build/', '/coverage/'];
if (skipPatterns.some(p => filePath.includes(p))) process.exit(0);

try { if (fs.statSync(filePath).size > 500 * 1024) process.exit(0); } catch { process.exit(0); }

let content;
try { content = fs.readFileSync(filePath, 'utf-8'); } catch { process.exit(0); }

// Tailwind default spacing scale
const SPACING_OK = new Set(['0', 'px', '0.5', '1', '1.5', '2', '2.5', '3', '3.5', '4', '5', '6', '7', '8', '9', '10', '11', '12', '14', '16', '20', '24', '28', '32', '36', '40', '44', '48', '52', '56', '60', '64', '72', '80', '96']);
const GAP_PREFERRED = new Set(['1', '2', '3', '4', '5', '6', '8']);
const TEXT_OK = new Set(['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl']);
const COLOR_FAMILIES = new Set(['slate', 'gray', 'zinc', 'neutral', 'stone', 'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose', 'white', 'black', 'transparent', 'current', 'inherit']);

const lines = content.split('\n');
const findings = [];
const firedRules = new Map(); // rule → Set<className>

function addFinding(rule, severity, msg, lineNum, excerpt, classVal) {
  if (!firedRules.has(rule)) firedRules.set(rule, new Set());
  const set = firedRules.get(rule);
  if (classVal && set.has(classVal)) return;
  if (classVal) set.add(classVal);
  findings.push({ rule, severity, msg, line: lineNum, excerpt: excerpt.slice(0, 80) });
}

const isMarketingPath = /(marketing|landing|hero|home|sections)/.test(filePath);

// --- RULES ---

// 1. ARBITRARY_VALUE (skipped in marketing paths)
if (!isMarketingPath) {
  const arbRe = /\b(p|m|pt|pb|pl|pr|px|py|mt|mb|ml|mr|mx|my|gap|space-[xy]|w|h|text|rounded)-\[([^\]]+)\]/g;
  lines.forEach((line, idx) => {
    let m;
    while ((m = arbRe.exec(line)) !== null) {
      const full = m[0];
      addFinding('ARBITRARY_VALUE', 'warn',
        `ua-ux: arbitrary Tailwind value '${full}' — use the scale (marketing/hero files exempt)`,
        idx + 1, line.trim(), full);
    }
  });
}

// 2. OFF_SCALE_SPACING
const spacingRe = /\b(p|m|px|py|pl|pr|pt|pb|mx|my|ml|mr|mt|mb|gap|space-x|space-y)-(\d+(?:\.\d+)?)\b/g;
lines.forEach((line, idx) => {
  let m;
  while ((m = spacingRe.exec(line)) !== null) {
    const prop = m[1];
    const val = m[2];
    if (!SPACING_OK.has(val)) {
      addFinding('OFF_SCALE_SPACING', 'warn',
        `ua-ux: off-scale spacing '${prop}-${val}' — use the Tailwind scale`,
        idx + 1, line.trim(), `${prop}-${val}`);
    }
  }
});

// 3. ODD_GAP (soft/info)
const gapRe = /\bgap-(\d+)\b/g;
lines.forEach((line, idx) => {
  let m;
  while ((m = gapRe.exec(line)) !== null) {
    const val = m[1];
    if (SPACING_OK.has(val) && !GAP_PREFERRED.has(val)) {
      addFinding('ODD_GAP', 'info',
        `ua-ux (soft): prefer gap-{1,2,4,6,8}, found 'gap-${val}'`,
        idx + 1, line.trim(), `gap-${val}`);
    }
  }
});

// 4. BAD_TEXT_SIZE
const textRe = /\btext-([a-z0-9]+(?:-[a-z0-9]+)*)\b/g;
lines.forEach((line, idx) => {
  let m;
  while ((m = textRe.exec(line)) !== null) {
    const suffix = m[1];
    // Compound suffix (contains '-') = semantic/color token (text-card-foreground,
    // text-muted-foreground, text-red-500, etc.), never a size. Skip.
    if (suffix.indexOf('-') !== -1) continue;
    const nonSizeSuffixes = new Set(['left', 'right', 'center', 'justify', 'balance', 'pretty', 'wrap', 'nowrap', 'ellipsis', 'clip', 'start', 'end', 'opacity', 'transparent', 'current', 'inherit', 'primary', 'secondary', 'tertiary', 'muted', 'accent', 'destructive', 'success', 'warning', 'foreground', 'background', 'border', 'ring', 'card', 'popover', 'input']);
    if (COLOR_FAMILIES.has(suffix)) continue;
    if (nonSizeSuffixes.has(suffix)) continue;
    if (TEXT_OK.has(suffix)) continue;
    // Numeric-only suffixes are colors (text-500 doesn't exist but text-red-500 does; the regex wouldn't catch that)
    if (/^\d+$/.test(suffix)) continue;
    addFinding('BAD_TEXT_SIZE', 'warn',
      `ua-ux: unknown text size 'text-${suffix}' — use xs/sm/base/lg/xl/2xl/3xl`,
      idx + 1, line.trim(), `text-${suffix}`);
  }
});

// 5. ARBITRARY_RADIUS
const radiusRe = /\brounded-\[([^\]]+)\]/g;
lines.forEach((line, idx) => {
  let m;
  while ((m = radiusRe.exec(line)) !== null) {
    addFinding('ARBITRARY_RADIUS', 'warn',
      `ua-ux: use rounded-{sm,md,lg,xl,2xl,3xl,full} — arbitrary radius breaks rhythm`,
      idx + 1, line.trim(), m[0]);
  }
});

// --- OUTPUT ---
if (findings.length === 0) process.exit(0);

console.log(`\n📐 SENSE 5 (RHYTHM) — ${path.basename(filePath)}`);
findings.forEach(f => {
  const prefix = f.severity === 'info' ? '○' : '•';
  const locHint = f.line > 0 ? ` L${f.line}` : '';
  console.log(`  ${prefix} [${f.rule}]${locHint} ${f.msg}`);
});

process.exit(0);
