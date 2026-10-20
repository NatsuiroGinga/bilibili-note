import { readFileSync } from 'fs';
import { basename, extname } from 'path';
import { apiRequest, loadConfig, resolveSpaceAndFolder, parseArgs, getDocumentUrl } from './utils.mjs';

// 上传本地文档到知了文档平台。
// .md（及其它文本文件）走 /document/create 建新文档；带 --document-id 时改为整篇覆盖那一篇。
// .html/.htm/.zip 走 /document/upload，可显式指定 --document-id 更新已有网页文档。
// .pdf/.doc/.docx/.ppt/.pptx 是二进制文件，走 /document/upload（multipart），仅支持创建。
//
// 注意：这里**不做「同名就更新」的猜测**。以前靠本地缓存按标题模糊匹配来决定更新哪篇，
// 缓存一旦过期就会覆盖掉别人的同名文档。要更新已有文档，请显式传 --document-id。

const USAGE = '用法: node upload-document.mjs <本地文件路径> [--title "自定义标题"] [--document-id doc_xxx] [--space-id sp_xxx] [--folder-id fd_xxx] [--tags "标签1,标签2"]';

const BINARY_EXTS = new Set(['.pdf', '.doc', '.docx', '.ppt', '.pptx']);
const WEB_DOCUMENT_EXTS = new Set(['.html', '.htm', '.zip']);

const args = parseArgs(process.argv);
const filePath = args._[0];

if (!filePath) {
  console.error(USAGE);
  process.exit(1);
}

const ext = extname(filePath).toLowerCase();

if (BINARY_EXTS.has(ext)) {
  await uploadBinaryDocument(filePath, ext);
} else if (WEB_DOCUMENT_EXTS.has(ext)) {
  await uploadWebDocument(filePath);
} else {
  await uploadMarkdownDocument(filePath);
}

async function uploadBinaryDocument(filePath, ext) {
  if (args['document-id']) {
    console.error('PDF/Word/PowerPoint 等二进制文档不支持通过 --document-id 重新上传更新');
    process.exit(1);
  }

  let buffer;
  try {
    buffer = readFileSync(filePath);
  } catch (err) {
    console.error(`读取文件失败: ${err.message}`);
    process.exit(1);
  }

  const fileSizeMB = buffer.length / (1024 * 1024);
  if (fileSizeMB > 20) {
    console.error(`文件过大: ${fileSizeMB.toFixed(1)}MB，上限 20MB`);
    process.exit(1);
  }

  const { spaceId, folderId } = await resolveSpaceAndFolder(args);
  const { apiKey, baseUrl } = loadConfig();
  const title = args.title || basename(filePath, ext);

  const form = new FormData();
  form.append('file', new Blob([buffer]), basename(filePath));
  form.append('spaceId', spaceId);
  form.append('folderId', folderId);

  if (args.tags) {
    const tags = typeof args.tags === 'string'
      ? args.tags.split(',').map(t => t.trim()).filter(Boolean)
      : [];
    if (tags.length > 0) {
      form.append('tags', JSON.stringify(tags));
    }
  }

  console.log(`上传文件: ${basename(filePath)} (${fileSizeMB.toFixed(2)}MB)`);
  console.log(`标题: ${title}`);
  console.log(`空间: ${spaceId}`);
  console.log(`文件夹: ${folderId}`);
  console.log('');

  let response;
  try {
    response = await fetch(`${baseUrl}/document/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}` },
      body: form,
    });
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

  if (json.code !== 0) {
    console.error(`上传失败: ${json.message || '未知错误'} (code=${json.code})`);
    process.exit(1);
  }

  const doc = json.data;

  // /document/upload 用上传文件名（而非 --title）生成远程标题，这里显式纠正为期望标题
  if (doc.title !== title) {
    await apiRequest('POST', '/document/update-metadata', { documentId: doc.id, title });
  }

  console.log(`上传成功`);
  console.log(`  ID:      ${doc.id}`);
  console.log(`  标题:    ${title}`);
  console.log(`  空间:    ${spaceId}`);
  console.log(`  文件夹:  ${folderId}`);
  if (doc.bossUrl) console.log(`  源文件:  ${doc.bossUrl}`);
  console.log(`  URL:     ${getDocumentUrl(doc.id)}`);
  console.log(`\n知识库同步为异步处理，搜索结果可能有几秒延迟`);
}

async function uploadWebDocument(filePath) {
  let buffer;
  try {
    buffer = readFileSync(filePath);
  } catch (err) {
    console.error(`读取文件失败: ${err.message}`);
    process.exit(1);
  }

  const fileSizeMB = buffer.length / (1024 * 1024);
  if (fileSizeMB > 20) {
    console.error(`文件过大: ${fileSizeMB.toFixed(1)}MB，上限 20MB`);
    process.exit(1);
  }

  const documentId = args['document-id'];
  let spaceId;
  let folderId;
  if (!documentId) {
    ({ spaceId, folderId } = await resolveSpaceAndFolder(args));
  }

  const { apiKey, baseUrl } = loadConfig();
  const form = new FormData();
  form.append('file', new Blob([buffer]), basename(filePath));
  if (documentId) {
    form.append('documentId', documentId);
  } else {
    form.append('spaceId', spaceId);
    form.append('folderId', folderId);
    const tags = parseTags(args.tags);
    if (tags.length > 0) form.append('tags', JSON.stringify(tags));
  }

  console.log(`${documentId ? '更新' : '上传'}网页文件: ${basename(filePath)} (${fileSizeMB.toFixed(2)}MB)`);
  if (documentId) {
    console.log(`文档: ${documentId}`);
    if (args.tags) console.log('提示: 网页文档更新会保留原标签，当前服务端忽略 --tags');
  } else {
    console.log(`空间: ${spaceId}`);
    console.log(`文件夹: ${folderId}`);
  }
  if (args.title) console.log('提示: 网页文档标题由页面或文件解析，当前服务端忽略 --title');
  console.log('');

  let response;
  try {
    response = await fetch(`${baseUrl}/document/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}` },
      body: form,
    });
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
  if (json.code !== 0) {
    console.error(`${documentId ? '更新' : '上传'}失败: ${json.message || '未知错误'} (code=${json.code})`);
    process.exit(1);
  }

  const doc = json.data;
  const resultDocumentId = doc.id || documentId;
  console.log(`${documentId ? '网页文档更新' : '网页文档上传'}成功`);
  console.log(`  ID:      ${resultDocumentId}`);
  if (doc.title) console.log(`  标题:    ${doc.title}`);
  if (doc.bossUrl) console.log(`  源文件:  ${doc.bossUrl}`);
  console.log(`  URL:     ${getDocumentUrl(resultDocumentId)}`);
  console.log('\n知识库同步为异步处理，搜索结果可能有几秒延迟');
}

function parseTags(value) {
  if (typeof value !== 'string') return [];
  return value.split(',').map((tag) => tag.trim()).filter(Boolean);
}

async function uploadMarkdownDocument(filePath) {
  let content;
  try {
    content = readFileSync(filePath, 'utf-8');
  } catch (err) {
    console.error(`读取文件失败: ${err.message}`);
    process.exit(1);
  }

  const title = args.title || basename(filePath, extname(filePath));
  const documentId = args['document-id'];

  if (documentId) {
    // 显式指定了要更新哪一篇：整篇覆盖
    console.log(`⚠️  将用本地文件整篇覆盖 ${documentId}（会重排全文、丢失划词评论锚点与样式）\n`);
    const result = await apiRequest('POST', '/document/update', { documentId, title, content });

    console.log(`文档更新成功`);
    console.log(`  ID:    ${result.id}`);
    console.log(`  标题:  ${result.title}`);
    console.log(`  更新:  ${result.mtime}`);
    console.log(`  URL:   ${getDocumentUrl(result.id)}`);
  } else {
    const { spaceId, folderId } = await resolveSpaceAndFolder(args);

    const result = await apiRequest('POST', '/document/create', {
      title,
      content,
      type: 'markdown',
      spaceId,
      folderId,
    });

    console.log(`文档创建成功`);
    console.log(`  ID:      ${result.id}`);
    console.log(`  标题:    ${result.title}`);
    console.log(`  作者:    ${result.owner}`);
    console.log(`  空间:    ${spaceId}`);
    console.log(`  文件夹:  ${folderId}`);
    console.log(`  创建:    ${result.ctime}`);
    console.log(`  URL:     ${getDocumentUrl(result.id)}`);
    console.log(`\n（要更新已有文档而不是新建，请传 --document-id doc_xxx）`);
  }

  console.log(`\n知识库同步为异步处理，搜索结果可能有几秒延迟`);
}
