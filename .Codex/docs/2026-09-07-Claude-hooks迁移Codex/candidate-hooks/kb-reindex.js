#!/usr/bin/env node
'use strict';

// Codex 适配：PostToolUse 的 apply_patch 输入是补丁文本，不再提供 Claude 的 file_path 字段。
const childProcess = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const researchRoot = path.join(os.homedir(), 'Dev', 'Research');
const mcpDir = path.join(researchRoot, '.knowledge-mcp');
const python = path.join(mcpDir, '.venv', 'bin', 'python');
const worker = path.join(mcpDir, 'auto_reindex.py');
const logDir = path.join(os.homedir(), 'Library', 'Application Support', 'research-knowledge');

function isKnowledgeEdit(command) {
  const files = [...command.matchAll(/^\*\*\* (?:Add|Update) File: (.+)$/gm)].map((match) => path.resolve(process.cwd(), match[1].trim()));
  return files.some((file) => file.startsWith(`${researchRoot}${path.sep}`) && !file.startsWith(`${mcpDir}${path.sep}`));
}

function launch() {
  if (!fs.existsSync(python) || !fs.existsSync(worker)) return;
  try {
    fs.mkdirSync(logDir, { recursive: true });
    const log = fs.openSync(path.join(logDir, 'auto_reindex.launch.log'), 'a');
    const child = childProcess.spawn(python, [worker], {
      detached: true,
      stdio: ['ignore', log, log],
      env: { ...process.env, PYTHONPATH: path.join(mcpDir, 'src') },
    });
    child.unref();
  } catch {}
}

let payload = {};
try { payload = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch {}
if (process.argv.includes('--if-kb-edit')) {
  const command = payload.tool_input?.command;
  if (typeof command === 'string' && isKnowledgeEdit(command)) launch();
} else {
  launch();
}
