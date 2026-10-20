import { apiRequest, resolveSpaceId, parseArgs } from './utils.mjs';

const args = parseArgs(process.argv);
const name = args.name;

if (!name) {
  console.error('用法: node create-folder.mjs --name "文件夹名称" [--space-id sp_xxx] [--parent-id fd_xxx] [--introduction "简介"]');
  process.exit(1);
}

const spaceId = await resolveSpaceId(args);

const body = { name };
if (args['parent-id']) body.parentId = args['parent-id'];
if (args.introduction) body.introduction = args.introduction;

const result = await apiRequest('POST', `/space/${spaceId}/create-folder`, body);

console.log(`\n文件夹创建成功`);
console.log(`  ID:      ${result.id}`);
console.log(`  名称:    ${result.name}`);
console.log(`  空间:    ${result.spaceId || spaceId}`);
if (result.parentId) console.log(`  父级:    ${result.parentId}`);
