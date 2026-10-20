import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

const args = parseArgs(process.argv);
const documentId = args._[0];

// 整篇覆盖是破坏性操作，只接受确切的 doc_xxx，不做按标题模糊定位
if (!documentId) {
  console.error('用法: node update-document.mjs <documentId> [--title "新标题"] [--content "新内容"]');
  console.error('      cat new.md | node update-document.mjs <documentId>');
  console.error('\ntitle / content 至少传一个。只知道标题时，先用 get-document.mjs --title "标题" 查到确切 ID。');
  console.error('注意：本命令是整篇覆盖，会重排全文并丢失划词评论锚点与样式。');
  console.error('     改局部请用 apply-document-patch.mjs，只改标题请用 update-metadata.mjs。');
  process.exit(1);
}

// content 优先参数，否则尝试 stdin。两者都没有时**不传 content 字段**——
// 服务端据此判断「不动正文」；传空字符串则是明确要求清空正文。
let content = args.content;
if (content === undefined && !process.stdin.isTTY) {
  content = await new Promise((resolve) => {
    let d = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', (chunk) => d += chunk);
    process.stdin.on('end', () => resolve(d));
  });
}

const body = { documentId };
if (args.title) body.title = args.title;
if (content !== undefined) body.content = content;

if (body.title === undefined && body.content === undefined) {
  console.error('错误: 至少需要 --title 或 --content 其中之一');
  process.exit(1);
}

if (body.content === '') {
  console.log('⚠️  content 为空字符串，将清空该文档的正文内容。\n');
}

const result = await apiRequest('POST', '/document/update', body);

console.log(`文档更新成功`);
console.log(`  ID:    ${result.id}`);
console.log(`  标题:  ${result.title}`);
console.log(`  更新:  ${result.mtime}`);
console.log(`  URL:   ${getDocumentUrl(result.id)}`);
