#!/usr/bin/env node
'use strict';

// Codex 仅把可确定拒绝的灾难性操作返回为 PreToolUse deny。
// 需要确认的操作交给 Codex 自身审批机制，避免输出尚不支持的 ask 决策。
const fs = require('fs');

let input = {};
try { input = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch {}

const toolName = input.tool_name || '';
const command = typeof input.tool_input?.command === 'string' ? input.tool_input.command : '';
const blockers = [
  /rm\s+-rf\s+\/(\s|$)/,
  /rm\s+--no-preserve-root/,
  /dd\s+if=\/dev\/(zero|random)/,
  />\s*\/dev\/(sd|nvme|vda)/,
  /mkfs\./,
  /rm\s+-rf?\s+\/(etc|usr|bin|sbin)(\/|\s|$)/,
  /rm\s+-rf\s+\/home\/[^\/\s]*\/?(\s|$)/,
  /rm\s+-rf\s+\/Users\/[^\/\s]*\/?(\s|$)/,
];

if (toolName === 'Bash' && blockers.some((pattern) => pattern.test(command))) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: '安全守卫拒绝灾难性命令。',
    },
  }));
}
