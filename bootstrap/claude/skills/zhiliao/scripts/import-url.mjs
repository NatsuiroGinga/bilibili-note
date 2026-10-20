import { apiRequest, getDocumentUrl, parseArgs, resolveSpaceAndFolder } from './utils.mjs';

const USAGE = '用法: node import-url.mjs <https-url> [--document-id doc_xxx] [--title "标题"] [--space-id sp_xxx] [--folder-id fd_xxx] [--tags "标签1,标签2"] [--target-ip 1.2.3.4]';
const args = parseArgs(process.argv);
const url = args._[0];

if (!url) {
  console.error(USAGE);
  process.exit(1);
}
if (url.length > 1024) {
  console.error('URL 无效: 长度不能超过 1024 个字符');
  process.exit(1);
}

try {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:') throw new Error('仅支持 https');
} catch (err) {
  console.error(`URL 无效: ${err.message}`);
  process.exit(1);
}

const documentId = args['document-id'];
const body = { url };
if (documentId) {
  body.documentId = documentId;
} else {
  const { spaceId, folderId } = await resolveSpaceAndFolder(args);
  body.spaceId = spaceId;
  body.folderId = folderId;
  if (args.title) body.title = args.title;
  if (args.tags) body.tags = parseTags(args.tags);
}
if (args['target-ip']) body.targetIp = args['target-ip'];

if (documentId && (args.title || args.tags)) {
  console.log('提示: URL 文档更新只更换 URL 并重新抓取，当前服务端会保留原标题与标签');
}

const result = await apiRequest('POST', '/document/from-url', body);
console.log(`${documentId ? 'URL 文档更新' : 'URL 文档创建'}任务已提交`);
console.log(`  Task ID: ${result.taskId}`);
if (documentId) console.log(`  文档:    ${getDocumentUrl(documentId)}`);
console.log(`\n查询状态: node get-web-import-status.mjs ${result.taskId}`);

function parseTags(value) {
  if (typeof value !== 'string') return [];
  return value.split(',').map((tag) => tag.trim()).filter(Boolean);
}
