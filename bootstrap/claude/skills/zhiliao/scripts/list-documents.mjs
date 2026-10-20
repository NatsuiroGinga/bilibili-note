import { apiRequest, parseArgs } from './utils.mjs';

const args = parseArgs(process.argv);
const folderId = args._[0] || args['folder-id'];

if (!folderId) {
  console.error('用法: node list-documents.mjs <folderId>');
  console.error('      node list-documents.mjs --folder-id fd_xxx');
  console.error('\n请先运行 list-folders.mjs 获取可用文件夹 ID');
  process.exit(1);
}

const documents = await apiRequest('GET', `/folder/${folderId}/documents`);

console.log(`文件夹 ${folderId} 下共 ${documents.length} 篇文档:\n`);
for (const doc of documents) {
  console.log(`  ${doc.id}  ${doc.title}  (owner: ${doc.owner || '-'})`);
}
