import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

const args = parseArgs(process.argv);
const documentId = args._[0];

// 写操作只接受确切的 doc_xxx：--title 在这里的语义是「新标题」，不做按标题查文档
if (!documentId) {
  console.error('用法: node update-metadata.mjs <documentId> [--title "新标题"] [--tags "标签1,标签2"]');
  console.error('\n至少需要 --title 或 --tags 其中之一');
  console.error('只知道标题时，先用 get-document.mjs --title "标题" 或 search-knowledge.mjs 查到确切 ID。');
  process.exit(1);
}

const body = { documentId };

const newTitle = args.title;
if (newTitle) body.title = newTitle;

// 标签：逗号分隔的字符串转数组
if (args.tags !== undefined) {
  const tags = typeof args.tags === 'string'
    ? args.tags.split(',').map(t => t.trim()).filter(Boolean)
    : [];
  body.tags = tags;
}

if (!body.title && body.tags === undefined) {
  console.error('错误: 至少需要 --title 或 --tags 其中之一');
  process.exit(1);
}

await apiRequest('POST', '/document/update-metadata', body);

console.log(`元数据更新成功`);
console.log(`  ID:    ${documentId}`);
console.log(`  URL:   ${getDocumentUrl(documentId)}`);
if (newTitle) console.log(`  标题:  ${newTitle}`);
if (body.tags) console.log(`  标签:  ${body.tags.join(', ')}`);
