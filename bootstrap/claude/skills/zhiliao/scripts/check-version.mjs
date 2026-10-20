import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { loadConfig } from './utils.mjs';

// skill 版本自检：读本地 SKILL.md 的 version，与服务端 /skill-version 比对，落后就提示用户升级。
// 设计为「本会话激活 skill 时跑一次」（由 SKILL.md 指令驱动），不写进 utils/apiRequest，避免给每个命令加延迟。
// best-effort：网络失败/超时/接口无数据一律静默退出 0，绝不阻断用户后续操作。

const TIMEOUT_MS = 3000;

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_MD_PATH = join(__dirname, '..', 'SKILL.md');

// 解析形如 "1.2.10" 的版本号，缺位补 0；非法返回 null
function parseVersion(v) {
  if (typeof v !== 'string') return null;
  const m = v.trim().match(/^(\d+)\.(\d+)\.(\d+)/);
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

// a < b 返回 -1，a > b 返回 1，相等 0
function compareVersion(a, b) {
  for (let i = 0; i < 3; i++) {
    if (a[i] < b[i]) return -1;
    if (a[i] > b[i]) return 1;
  }
  return 0;
}

function readLocalVersion() {
  try {
    const raw = readFileSync(SKILL_MD_PATH, 'utf-8');
    // 只在 frontmatter（第一段 --- 之间）里找 version:
    const fm = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    const scope = fm ? fm[1] : raw;
    const m = scope.match(/^version:\s*(.+)$/m);
    return m ? m[1].trim() : null;
  } catch {
    return null;
  }
}

async function fetchRemoteVersion() {
  const { apiKey, baseUrl } = loadConfig();
  const url = `${baseUrl}/skill-version`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      headers: { Authorization: `Bearer ${apiKey}` },
      signal: controller.signal,
    });
    const json = await resp.json();
    if (json.code !== 0 || !json.data) return null;
    return json.data.version || null;
  } catch {
    return null; // 网络错误 / 超时 / 解析失败 → 静默跳过
  } finally {
    clearTimeout(timer);
  }
}

const local = readLocalVersion();
const remote = await fetchRemoteVersion();

const localV = parseVersion(local);
const remoteV = parseVersion(remote);

// 任一版本拿不到就静默退出，不打扰用户
if (!localV || !remoteV) {
  process.exit(0);
}

if (compareVersion(localV, remoteV) < 0) {
  console.error('');
  console.error('⚠️  知了 skill 有新版本可用');
  console.error(`    当前版本: ${local}    最新版本: ${remote}`);
  console.error('');
  console.error('    新版本可能包含新功能或问题修复，建议升级：');
  console.error('    1. 在 Claude Code 中执行 /plugin');
  console.error('    2. 选中 zhiliao（marketplace: common）→ Update');
  console.error('    3. Update 完成后执行 reload-plugin 使其在本会话生效');
  console.error('');
  console.error('    （升级前仍可正常使用，此提示不影响当前操作）');
} else {
  console.log(`知了 skill 已是最新版本（${local}）`);
}

process.exit(0);
