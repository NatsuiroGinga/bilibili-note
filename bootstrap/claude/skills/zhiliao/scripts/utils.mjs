import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
export const DATA_DIR = join(__dirname, '..', 'data');
export const CONFIG_PATH = join(DATA_DIR, 'config.json');
// 运行时工作目录下的裸 key 文件（优先级最高），与 Python 版 skill 对齐
export const CWD_KEY_PATH = join(process.cwd(), 'zhiliao_docs', 'apikey');

const DEFAULT_BASE_URL = 'https://aistudio.bilibili.co/api/v1/openapi';
const WEB_BASE_URL = 'https://aistudio.bilibili.co';

const isPlaceholderKey = (k) =>
  !k || typeof k !== 'string' || k === 'aist_' || /^aist_x+$/i.test(k) || k.length < 12;

let configHintShown = false;

// 站内规范地址只有 /wiki/{id} 一种：文档 doc_、空间 sp_、目录 fd_ 共用它，由 id 前缀分流。
// 原先给的是 /share/{id}——那是文档分享页，打得开但不是文档的常规视图（没有侧栏、进不去编辑）。
export function getDocumentUrl(id) {
  return `${WEB_BASE_URL}/wiki/${id}`;
}

export function loadConfig() {
  let config = {};
  try {
    config = JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
  } catch {}

  const envKey = process.env.ZHILIAO_API_KEY;
  const fileKey = config.apiKey;
  let cwdKey = null;
  try {
    cwdKey = readFileSync(CWD_KEY_PATH, 'utf-8').trim();
  } catch {}

  let apiKey = null;
  let source = null;

  // 优先级：<cwd>/zhiliao_docs/apikey > ZHILIAO_API_KEY 环境变量 > config.json
  if (!isPlaceholderKey(cwdKey)) {
    apiKey = cwdKey;
    source = 'cwdfile';
  } else if (!isPlaceholderKey(envKey)) {
    apiKey = envKey;
    source = 'env';
  } else if (!isPlaceholderKey(fileKey)) {
    apiKey = fileKey;
    source = 'config';
  }

  if (!apiKey) {
    console.error(
      '错误: 未配置有效的知了 API Key（zhiliao_docs/apikey、ZHILIAO_API_KEY 环境变量与 config.json 均缺失或为占位符）',
    );
    console.error('');
    console.error('请按以下任一方式配置（优先级从高到低）：');
    console.error('');
    console.error(`【方式 1 · 最高优先级】在当前工作目录下创建 ${CWD_KEY_PATH}`);
    console.error('  文件内容为真实 key（aist_ 开头的字符串），无需其它字段');
    console.error('');
    console.error(
      '【方式 2】在 ~/.claude/settings.json 中加入 env 配置（适用于所有 Claude Code 会话）：',
    );
    console.error('  {');
    console.error('    "env": {');
    console.error('      "ZHILIAO_API_KEY": "aist_xxxxxxxxxxxx"');
    console.error('    }');
    console.error('  }');
    console.error('  配置后需重启 Claude Code 会话才会生效');
    console.error('  或在 shell 配置（~/.zshrc / ~/.bashrc）中 export ZHILIAO_API_KEY 后重开终端');
    console.error('');
    console.error(`【方式 3】编辑 ${CONFIG_PATH}`);
    console.error('  把 apiKey 字段改为真实值（aist_ 开头的字符串）');
    console.error('');
    console.error('如何申请：联系 aistudio.bilibili.co 平台管理员获取 API Key');
    process.exit(1);
  }

  if (source === 'config' && !configHintShown) {
    console.error(
      '提示: 当前从 config.json 读取 API Key，建议改用环境变量 ZHILIAO_API_KEY 以方便跨项目管理（推荐写入 ~/.claude/settings.json 的 env）',
    );
    configHintShown = true;
  }

  return {
    apiKey,
    baseUrl: config.baseUrl || DEFAULT_BASE_URL,
    defaultSpaceId: config.defaultSpaceId || null,
    defaultFolderId: config.defaultFolderId || null,
  };
}

export async function apiRequest(method, path, body) {
  const config = loadConfig();
  const url = config.baseUrl + path;

  const init = {
    method,
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
  if (body && method !== 'GET') {
    init.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, init);
  } catch (err) {
    console.error(`网络错误: ${err.message}`);
    process.exit(1);
  }

  const raw = await response.text();
  let json;
  try {
    json = JSON.parse(raw);
  } catch {
    console.error(`响应解析失败 (HTTP ${response.status}): ${raw.slice(0, 500)}`);
    process.exit(1);
  }

  if (json.code === 401 || response.status === 401) {
    console.error('错误: API Key 无效或已过期');
    console.error(
      '请检查 ZHILIAO_API_KEY 环境变量（推荐在 ~/.claude/settings.json 的 env 中配置），或更新 data/config.json 中的 apiKey',
    );
    process.exit(1);
  }
  if (json.code === 403) {
    console.error(`错误: ${json.message || '无权限，请检查请求参数是否正确'} (${method} ${path})`);
    process.exit(1);
  }
  if (json.code === 404) {
    console.error(`错误: ${json.message || '资源不存在'} (${method} ${path})`);
    if (body) {
      const ids = ['spaceId', 'folderId', 'documentId']
        .filter((k) => body[k])
        .map((k) => `${k}=${body[k]}`)
        .join(', ');
      if (ids) console.error(`  请求中的 ID: ${ids}`);
    }
    console.error('可能原因: 空间/文件夹/文档已被删除或迁移；或当前 API Key 无权访问');
    process.exit(1);
  }
  if (json.code === 400) {
    console.error(`参数错误: ${json.message || '请检查请求参数'} (${method} ${path})`);
    if (body) {
      const ids = ['spaceId', 'folderId', 'documentId']
        .filter((k) => body[k])
        .map((k) => `${k}=${body[k]}`)
        .join(', ');
      if (ids) console.error(`  请求中的 ID: ${ids}`);
    }
    process.exit(1);
  }
  if (json.code !== 0) {
    console.error(
      `请求失败 (code=${json.code}, HTTP ${response.status}): ${json.message || '未知错误'}`,
    );
    process.exit(1);
  }

  return json.data;
}

/**
 * 按标题找 documentId：走知识库语义搜索，返回 { documentId, title } 或 null。
 *
 * 这里刻意不做任何本地缓存。曾经有一份 documents.json 缓存做标题模糊匹配，问题是它会过期——
 * 用户在网页上改了标题、删了文档、或者别人建了同名文档，缓存都感知不到，而一旦匹配错，
 * 后续的写操作就直接改到别人的文档上。查一次接口的成本远低于改错文档的代价。
 *
 * 即便如此，语义搜索也只是「猜」，所以只给**只读**场景用；写操作一律要求传 doc_xxx。
 */
export async function findDocumentByTitle(title) {
  const result = await apiRequest('POST', '/knowledge/search', {
    query: title,
    limit: 3,
    source: ['doc'],
  });
  const match = result?.results?.[0];
  if (!match?.sourceId) return null;
  return { documentId: match.sourceId, title: match.title, score: match.score };
}

/** 解析 spaceId：命令行参数 > config 默认值 > 接口里恰好只有一个空间时自动选 */
export async function resolveSpaceId(args) {
  const config = loadConfig();
  const spaceId = args['space-id'] || args._?.[0] || config.defaultSpaceId;
  if (spaceId) return spaceId;

  const spaces = await apiRequest('GET', '/spaces');
  if (spaces.length === 1) {
    console.log(`自动选择唯一空间: ${spaces[0].name} (${spaces[0].id})`);
    return spaces[0].id;
  }
  if (spaces.length === 0) {
    console.error('错误: 当前 API Key 没有可访问的空间，请联系平台管理员确认 Token 的空间授权');
    process.exit(1);
  }
  console.error('错误: 存在多个空间，请通过 --space-id 指定，或在 config.json 中设置 defaultSpaceId');
  console.error('可用空间:');
  for (const s of spaces) console.error(`  ${s.id}: ${s.name}`);
  process.exit(1);
}

/**
 * 解析 spaceId 和 folderId：命令行参数 > config 默认值 > 实时查接口。
 * folderId 未指定时取该空间的根目录（name 为 "/" 且 parentId 为空的那个）。
 */
export async function resolveSpaceAndFolder(args) {
  const config = loadConfig();
  const spaceId = await resolveSpaceId(args);

  let folderId = args['folder-id'] || config.defaultFolderId;
  if (!folderId) {
    const folders = await apiRequest('GET', `/space/${spaceId}/folders`);
    const root = folders.find((f) => f.name === '/' && (f.parentId === '' || f.parentId == null));
    if (!root) {
      console.error('错误: 未找到根目录文件夹。请通过 --folder-id 指定目标文件夹');
      console.error('可用文件夹:');
      for (const f of folders) console.error(`  ${f.id}: ${f.name}`);
      process.exit(1);
    }
    folderId = root.id;
    console.log(`自动选择根目录: ${root.name} (${folderId})`);
  }

  return { spaceId, folderId };
}

export function parseArgs(argv) {
  const args = argv.slice(2);
  const result = { _: [] };
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith('--')) {
        result[key] = next;
        i++;
      } else {
        result[key] = true;
      }
    } else {
      result._.push(args[i]);
    }
  }
  return result;
}
