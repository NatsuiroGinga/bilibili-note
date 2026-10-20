import { apiRequest, findDocumentByTitle, parseArgs, getDocumentUrl } from './utils.mjs';

const args = parseArgs(process.argv);
let documentId = args._[0];

if (!documentId && args.title) {
  const match = await findDocumentByTitle(args.title);
  if (!match) {
    console.error(`错误: 未搜索到标题匹配 "${args.title}" 的文档`);
    process.exit(1);
  }
  documentId = match.documentId;
  // 语义搜索是「猜」，把命中的标题打出来让人/agent 能核对是不是想要的那篇
  console.log(`搜索匹配: "${match.title}" (score: ${match.score}) -> ${match.documentId}\n`);
}

if (!documentId) {
  console.error('用法: node get-document.mjs <documentId>');
  console.error('      node get-document.mjs --title "标题"    # 语义搜索，结果仅供核对');
  process.exit(1);
}

const result = await apiRequest('GET', `/document/${documentId}`);

console.log(`标题:    ${result.title}`);
console.log(`ID:      ${result.id}`);
console.log(`URL:     ${getDocumentUrl(result.id)}`);
console.log(`作者:    ${result.owner}`);
if (result.folder) {
  console.log(`空间:    ${result.folder.spaceId}`);
  console.log(`文件夹:  ${result.folder.name} (${result.folder.folderId})`);
}
console.log(`创建:    ${result.ctime}`);
console.log(`更新:    ${result.mtime}`);
console.log(`\n--- 正文 ---\n`);
console.log(result.markdown || result.content || '(空)');
