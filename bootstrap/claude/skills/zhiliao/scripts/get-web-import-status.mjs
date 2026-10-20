import { apiRequest, getDocumentUrl } from './utils.mjs';

const taskId = process.argv[2];
if (!taskId) {
  console.error('用法: node get-web-import-status.mjs <taskId>');
  process.exit(1);
}

const result = await apiRequest('GET', `/document/web-import/status/${encodeURIComponent(taskId)}`);
console.log(`状态: ${result.status}`);
if (result.kind) console.log(`类型: ${result.kind}`);
if (result.doc) {
  const documentId = result.doc.documentId || result.doc.id;
  if (documentId) {
    console.log(`文档 ID: ${documentId}`);
    console.log(`URL: ${getDocumentUrl(documentId)}`);
  }
  if (result.doc.title) console.log(`标题: ${result.doc.title}`);
  if (result.doc.sourceUrl || result.doc.url) console.log(`来源: ${result.doc.sourceUrl || result.doc.url}`);
  if (result.doc.contentFetchFailed) console.log('警告: 文档已创建，但正文抓取失败');
}
if (result.error) console.log(`错误: ${result.error}`);
if (result.status === 'failed') process.exitCode = 1;
