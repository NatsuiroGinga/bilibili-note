#!/usr/bin/env node
/**
 * UserPromptSubmit：注入轻量技能路由规则。
 */

const fs = require('fs');

let input = {};
try {
  const stdinData = fs.readFileSync(0, 'utf8');
  if (stdinData.trim()) {
    input = JSON.parse(stdinData);
  }
} catch {
  // 输入异常时继续使用空提示，避免钩子阻塞用户请求。
}

const userPrompt = typeof input.user_prompt === 'string' ? input.user_prompt : '';

// 单段斜杠输入视为命令；包含后续路径分隔符时仍按普通提示处理。
if (userPrompt.startsWith('/') && !userPrompt.slice(1).includes('/')) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

const systemMessage = [
  '技能路由：依赖本会话已加载的技能清单，静默选择完成本轮任务所需的最少且直接相关技能。',
  '若有专用 Skill 工具则调用；否则只读取所选技能的 SKILL.md。',
  '无匹配技能时直接执行。不要枚举技能、输出路由过程，或在同一轮重复读取技能。'
].join('\n');

console.log(JSON.stringify({ continue: true, systemMessage }));
process.exit(0);
