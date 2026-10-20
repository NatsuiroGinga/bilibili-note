import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

// 头尾快速插入：把一段内容插到文档开头(prepend)或末尾(append)。
// 与补丁编辑相比**免去先 get 全文找锚点**——位置固定（文首/文末）。
// documentId 走参数，插入内容走 stdin。身份由 API Key 决定（仅文档所有者可编辑）。
//
// 内容格式 = 无损 markdown/html（与 get-lossless-markdown / apply-document-patch 同源）：
//   标题 #、列表 -/1.、表格用 <table>（不是 GFM |竖线|）、颜色 <span style>、
//   @提及 <mention data-attrs>、划词评论 <comment data-attrs>。块级节点天然分段，无需手动留空行。
//
// 用法：
//   echo '## 新章节\n\n正文' | node apply-document-edge.mjs <documentId> --append
//   echo '# 置顶公告'        | node apply-document-edge.mjs <documentId> --prepend

const args = parseArgs(process.argv);
const documentId = args._[0];

// 方向：--prepend 插到开头，--append（默认）追加到末尾。
const edge = args.prepend ? 'prepend' : 'append';

// 写操作只接受确切的 doc_xxx——按标题模糊定位有改到别人文档的风险
if (!documentId) {
  console.error('用法: echo "内容" | node apply-document-edge.mjs <documentId> [--append|--prepend]');
  console.error('\n插入内容通过 stdin 传入，格式为无损 markdown/html（表格用 <table>，非 |竖线|）');
  console.error('默认追加到末尾(append)，加 --prepend 则插到开头');
  console.error('只知道标题时，先用 get-document.mjs --title "标题" 查到确切 ID。');
  process.exit(1);
}

if (process.stdin.isTTY) {
  console.error('错误: 插入内容需通过 stdin 传入，例如：');
  console.error('  printf \'## 新章节\\n\\n正文一段\' | node apply-document-edge.mjs doc_xxx --append');
  process.exit(1);
}

const content = await new Promise((resolve) => {
  let d = '';
  process.stdin.setEncoding('utf-8');
  process.stdin.on('data', (chunk) => (d += chunk));
  process.stdin.on('end', () => resolve(d));
});

if (!content.trim()) {
  console.error('错误: 插入内容为空');
  process.exit(1);
}

const routePath = edge === 'prepend' ? 'apply-prepend-v2' : 'apply-append-v2';
await apiRequest('POST', `/document/${documentId}/${routePath}`, { content });

console.log(`已${edge === 'prepend' ? '插入到文档开头' : '追加到文档末尾'}`);
console.log(`文档ID: ${documentId}`);
console.log(`URL:    ${getDocumentUrl(documentId)}`);
