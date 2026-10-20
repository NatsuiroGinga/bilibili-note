import { apiRequest, findDocumentByTitle, parseArgs } from './utils.mjs';

// 获取文档的「无损 markdown」（带 HTML 标签：复杂表格 <table>、颜色 <span style>、私有属性
// data-attrs 等都保真）。这份 markdown 能无损还原回文档，是 apply-document-patch 的编辑基准。
//
// 长文档友好：默认自适应——全文不超阈值直接返回全文；超阈值则返回「标题目录 + 总长度」，
// 让你先看结构、再用 --section 取具体章节，避免一次把超长全文读进上下文。
//
// 用法：
//   node get-lossless-markdown.mjs <documentId>              # 默认：短文档返回全文，长文档返回目录
//   node get-lossless-markdown.mjs <documentId> --full       # 强制返回全文（不论长度）
//   node get-lossless-markdown.mjs <documentId> --section "1.1 大盘数据"  # 只取该标题的章节
//   node get-lossless-markdown.mjs --title "文档标题" [--full|--section ...]
//
// 典型流程：先默认调用看全文/目录 → 长文档按目录用 --section 取要改的章节 → 本地改文本生成
// *** Begin Patch 补丁 → apply-document-patch 提交（补丁靠文本锚点定位，无需页号/章节号）。

const args = parseArgs(process.argv);
let documentId = args._[0];

if (!documentId && args.title) {
  const match = await findDocumentByTitle(args.title);
  if (!match) {
    console.error(`错误: 未搜索到标题匹配 "${args.title}" 的文档`);
    process.exit(1);
  }
  documentId = match.documentId;
  // 语义搜索是「猜」，把命中的标题打出来——基于错文档写的补丁一定匹配失败
  console.log(`搜索匹配: "${match.title}" (score: ${match.score}) -> ${match.documentId}\n`);
}

if (!documentId) {
  console.error('用法: node get-lossless-markdown.mjs <documentId> [--full] [--section "标题"]');
  console.error('      node get-lossless-markdown.mjs --title "标题" [--full] [--section "标题"]');
  console.error('\n默认短文档返回全文、长文档返回目录；--section 取单个章节；--full 强制全文。');
  process.exit(1);
}

const params = new URLSearchParams();
if (args.section) params.set('section', String(args.section));
if (args.full) params.set('full', 'true');
const qs = params.toString();
const data = await apiRequest('GET', `/document/${documentId}/lossless-markdown${qs ? `?${qs}` : ''}`);

console.log(`标题:    ${data.title}`);
console.log(`文档ID:  ${data.documentId}`);
console.log(`总长度:  ${data.totalLength} 字符`);

if (data.mode === 'outline') {
  console.log(`\n${data.hint}\n`);
  console.log('--- 标题目录 ---');
  for (const e of data.outline) {
    console.log(`${'  '.repeat(Math.max(0, e.level - 1))}${'#'.repeat(e.level)} ${e.text}`);
  }
  console.log('\n下一步：node get-lossless-markdown.mjs ' + documentId + ' --section "上面某个标题原文"');
} else if (data.mode === 'section') {
  console.log(`章节:    ${data.section}`);
  console.log(`\n--- 该章节无损 markdown（基于此生成补丁；用 apply-document-patch 提交）---\n`);
  console.log(data.markdown);
} else {
  console.log(`\n--- 无损 markdown（基于此生成补丁；改动请用 apply-document-patch 提交）---\n`);
  console.log(data.markdown);
}
