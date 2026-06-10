#!/usr/bin/env node
// Claude Code status line script

const { execFileSync } = require('child_process');
const os = require('os');

const RESET = '\x1b[0m';

// Color for a usage percentage: green < 50, amber < 80, red otherwise.
function usageColor(pct) {
  if (pct >= 80) return '\x1b[38;2;224;108;117m';
  if (pct >= 50) return '\x1b[38;2;229;192;123m';
  return '\x1b[38;2;152;195;121m';
}

// Format a unix-epoch reset time as 'HH:MM' (today) or 'Mon HH:MM' (later).
function fmtReset(ts) {
  if (ts == null) return '';
  const d = new Date(ts * 1000);
  const now = new Date();
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const sameDay = d.getFullYear() === now.getFullYear()
    && d.getMonth() === now.getMonth()
    && d.getDate() === now.getDate();
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return sameDay ? `${hh}:${mm}` : `${days[d.getDay()]} ${hh}:${mm}`;
}

// One usage segment, e.g. '5 Hour Usage: 4% -> 11:30'. Empty string if absent.
function usageSegment(label, win) {
  if (!win || win.used_percentage == null) return '';
  const pct = Math.round(win.used_percentage);
  const labelColor = '\x1b[38;2;204;153;51m';
  const dim = '\x1b[38;2;130;130;130m';
  const reset = fmtReset(win.resets_at);
  const tail = reset ? ` ${dim}→ ${reset}${RESET}` : '';
  return `${labelColor}${label}:${RESET} ${usageColor(pct)}${pct}%${RESET}${tail}`;
}

let input = '';
process.stdin.on('data', chunk => (input += chunk));
process.stdin.on('end', () => {
  let data = {};
  try { data = JSON.parse(input); } catch { }

  const cwd = data.workspace?.current_dir || data.cwd || '';
  const model = data.model?.display_name || '';
  const usedPct = data.context_window?.used_percentage;
  const fiveHour = data.rate_limits?.five_hour;
  const sevenDay = data.rate_limits?.seven_day;
  const vimMode = data.vim?.mode || '';

  // Shorten the cwd: replace $HOME with ~
  const home = os.homedir();
  const shortCwd = cwd && home && cwd.startsWith(home) ? '~' + cwd.slice(home.length) : cwd;

  // Git branch (skip optional locks to avoid blocking)
  let gitBranch = '';
  if (cwd) {
    const gitOpts = { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] };
    try {
      gitBranch = execFileSync('git', ['-C', cwd, 'symbolic-ref', '--short', 'HEAD'], gitOpts).trim();
    } catch {
      try {
        gitBranch = execFileSync('git', ['-C', cwd, 'rev-parse', '--short', 'HEAD'], gitOpts).trim();
      } catch { }
    }
  }

  // Line 1: directory, git branch, model, context usage, vim mode
  let line1 = '';
  if (shortCwd) line1 = shortCwd;
  if (gitBranch) line1 += `  ${gitBranch}`;
  if (model) line1 += `  ${model}`;
  if (usedPct != null) line1 += `  ctx:${Math.round(usedPct)}%`;
  if (vimMode) line1 += `  [${vimMode}]`;

  // Line 2: usage limits (Claude.ai Pro/Max only; each window may be absent)
  const line2 = [
    usageSegment('5 Hour Usage', fiveHour),
    usageSegment('7 Day Usage', sevenDay),
  ].filter(Boolean).join('  ');

  process.stdout.write(line2 ? `${line1}\n${line2}` : line1);
});
