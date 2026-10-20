import { apiRequest, parseArgs } from './utils.mjs';

const args = parseArgs(process.argv);
const documentId = args._[0];

// 删除是不可逆的，不接受按标题模糊定位——必须传确切的 doc_xxx
if (!documentId) {
  console.error('用法: node delete-document.mjs <documentId>');
  console.error('\n只接受 doc_xxx 形式的文档 ID。只知道标题时，先用 get-document.mjs --title "标题"');
  console.error('或 search-knowledge.mjs 查到确切 ID 并核对无误，再来删除。');
  process.exit(1);
}

await apiRequest('POST', '/document/delete', { documentId });

console.log(`文档已删除: ${documentId}`);
