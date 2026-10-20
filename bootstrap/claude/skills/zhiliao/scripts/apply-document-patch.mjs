import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

// 通过 *** Begin Patch ... *** End Patch 文本补丁增量编辑文档（apply-edit-v2）。
// documentId 走参数，补丁走 stdin。身份由 API Key 决定（仅文档所有者可编辑），无需 username。
//
// 补丁格式（OpenAI apply_patch 风格，基于 get-lossless-markdown 的输出定位）：
//
//   *** Begin Patch
//   @@
//    <上下文行，前缀一个空格，保持不变，用于唯一定位>
//   -<要删除的行，前缀 ->
//   +<要新增的行，前缀 +>
//   *** End Patch
//
// 两个标记各自独占一行、顶格写；服务端按整行识别边界，正文里出现 *** End Patch 字样不会截断补丁。
//
// 服务端会：在无损 markdown 里按上下文锚唯一匹配 → 应用补丁 → 结构化 diff → 最小变更写回。
// 若锚点在文档中匹配到 0 处或多处，会报错（不猜、不乱改），此时请扩大上下文行或核对原文。

const args = parseArgs(process.argv);
const documentId = args._[0];

// 写操作只接受确切的 doc_xxx——按标题模糊定位有改到别人文档的风险
if (!documentId) {
  console.error('用法: cat patch.txt | node apply-document-patch.mjs <documentId>');
  console.error('\n补丁通过 stdin 传入，格式为 *** Begin Patch ... *** End Patch');
  console.error('先用 get-lossless-markdown 拿到编辑基准，再据此生成补丁');
  console.error('只知道标题时，先用 get-document.mjs --title "标题" 查到确切 ID。');
  process.exit(1);
}

if (process.stdin.isTTY) {
  console.error('错误: 补丁需通过 stdin 传入，例如：');
  console.error('  printf \'*** Begin Patch\\n@@\\n-旧文案\\n+新文案\\n*** End Patch\\n\' | node apply-document-patch.mjs doc_xxx');
  process.exit(1);
}

const patch = await new Promise((resolve) => {
  let d = '';
  process.stdin.setEncoding('utf-8');
  process.stdin.on('data', (chunk) => (d += chunk));
  process.stdin.on('end', () => resolve(d));
});

// 与服务端一致：按「整行」识别边界（只允许行尾空白），不用 includes 做子串匹配——
// 否则正文里出现 *** End Patch 字样会被误判，而缩进/同行书写的标记又检不出来。
const hasMarkerLine = (marker) => patch.split('\n').some((l) => l.trimEnd() === marker);
if (!hasMarkerLine('*** Begin Patch') || !hasMarkerLine('*** End Patch')) {
  console.error('错误: *** Begin Patch / *** End Patch 必须各自独占一行、顶格写（行首不留空格、行尾不接其他内容）');
  process.exit(1);
}

await apiRequest('POST', `/document/${documentId}/apply-edit-v2`, { patch });

console.log(`补丁已应用`);
console.log(`文档ID: ${documentId}`);
console.log(`URL:    ${getDocumentUrl(documentId)}`);
console.log(`\n提示：可用 get-lossless-markdown ${documentId} 查看修改后的内容`);
