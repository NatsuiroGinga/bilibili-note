#!/usr/bin/env node
'use strict';

// 按 Codex 钩子事件补充与当前操作直接相关的规则片段。
const fs = require('fs');
const os = require('os');
const path = require('path');

const bundleDir = path.join(__dirname, 'rule-bundles');
const totalLimit = 9500;
const fileTool = 'apply_patch';
const ignoredProbe = /(?:which|type|man|whatis|help|alias|command\s+-v)\s+\S*(?:find|grep|sed)/g;
const bashHead = /(?:^|[;&|()]|\$\()\s*(?:sudo\s+|env\s+|xargs\s+)?(?:find|grep)\b/;
const gitSubcommand = /\bgit\s+(?:commit|revert|push|merge|rebase|branch|checkout\s+-b|switch\s+-c)\b/;

const groups = [
  {
    name: 'search-tools', max: 600, dedupe: false,
    command: (command) => {
      const sanitized = command.replace(ignoredProbe, '');
      return !( /\bgit\s+grep\b/.test(sanitized) && !/\s(find|^find)\b/.test(sanitized)) && bashHead.test(sanitized);
    },
    prompt: (prompt) => /(?:用|使用|通过|改用|换成)\s*[`'"]?(?:find|grep)\b/.test(prompt) || /\b(?:find|grep)\b\s*(?:-|\/|\.|["'])/.test(prompt),
  },
  {
    name: 'file-edit-tools', max: 600, dedupe: false,
    command: (command) => {
      const sanitized = command.replace(ignoredProbe, '');
      return /\bsed\b/.test(sanitized) && (/(?:^|\s)-i(?:\s|=|$)|--in-place/.test(sanitized) || /\bsed\b/.test(sanitized.replace(/\bsed\s+-n\s+(?:"[^"]*"|'[^']*')/g, '')));
    },
    prompt: (prompt) => /\bsed\b/.test(prompt.replace(ignoredProbe, '')),
  },
  {
    name: 'git-workflow', max: 600, dedupe: false,
    command: (command) => gitSubcommand.test(command),
    prompt: (prompt) => /\bgit\s+commit\b/.test(prompt) || (/(?:提交|[Cc]ommit)/.test(prompt) && /(?:代码|改动|修改|分支|合并|推送|push|MR|PR|git)/i.test(prompt)),
  },
  { name: 'go-rules', max: 9000, dedupe: true, file: /\.go$/i },
  { name: 'python-ml', max: 9000, dedupe: true, file: /(?:\.pyi?|\.ipynb|pyproject\.toml|requirements[^/]*\.txt|setup\.py)$/i },
];

function readBundle(name, limit) {
  try { return fs.readFileSync(path.join(bundleDir, `${name}.md`), 'utf8').trim().slice(0, limit); } catch { return ''; }
}

function statePath(sessionId) {
  const safe = String(sessionId).replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 80);
  return path.join(os.tmpdir(), 'codex-rule-inject', `${safe}.json`);
}

function wasInjected(sessionId, name) {
  if (!sessionId) return false;
  try { return JSON.parse(fs.readFileSync(statePath(sessionId), 'utf8')).done.includes(name); } catch { return false; }
}

function markInjected(sessionId, names) {
  if (!sessionId || names.length === 0) return;
  try {
    const target = statePath(sessionId);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    let state = { v: 1, done: [] };
    try { state = JSON.parse(fs.readFileSync(target, 'utf8')); } catch {}
    for (const name of names) if (!state.done.includes(name)) state.done.push(name);
    const temporary = `${target}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify(state));
    fs.renameSync(temporary, target);
  } catch {}
}

function changedFiles(command) {
  const matches = command.matchAll(/^\*\*\* (?:Add|Update) File: (.+)$/gm);
  return [...matches].map((match) => match[1].trim());
}

function main() {
  let input = {};
  try { input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch { return; }
  const sessionId = input.session_id || '';
  const matches = [];
  const isToolEvent = typeof input.tool_name === 'string';

  for (const group of groups) {
    let hit = false;
    if (isToolEvent && input.tool_name === 'Bash' && typeof input.tool_input?.command === 'string' && group.command) {
      hit = group.command(input.tool_input.command);
    } else if (isToolEvent && input.tool_name === fileTool && typeof input.tool_input?.command === 'string' && group.file) {
      hit = changedFiles(input.tool_input.command).some((file) => group.file.test(file));
    } else if (!isToolEvent && typeof input.prompt === 'string' && group.prompt) {
      hit = group.prompt(input.prompt);
    }
    if (hit && !(group.dedupe && wasInjected(sessionId, group.name))) matches.push(group);
  }

  const text = matches.map((group) => readBundle(group.name, group.max)).filter(Boolean).join('\n\n').slice(0, totalLimit);
  if (!text) return;
  markInjected(sessionId, matches.filter((group) => group.dedupe).map((group) => group.name));
  const event = isToolEvent ? 'PreToolUse' : 'UserPromptSubmit';
  console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: event, additionalContext: text } }));
}

try { main(); } catch { process.exitCode = 0; }
