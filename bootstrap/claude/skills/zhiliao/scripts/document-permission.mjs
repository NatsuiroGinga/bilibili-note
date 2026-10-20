import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

// 文档权限与协作者管理。
//
// 访问模式（accessMode）：
//   OPEN_EDIT      空间成员都可编辑
//   OPEN_READONLY  空间成员只能看
//   WHITELIST_ONLY 仅文档所有者与协作者名单内的人可见
//
// 用法：
//   node document-permission.mjs <documentId> --get                          # 看访问模式与自己的权限
//   node document-permission.mjs <documentId> --set-mode OPEN_READONLY       # 改访问模式
//   node document-permission.mjs <documentId> --list                         # 看协作者名单
//   node document-permission.mjs <documentId> --add guwenjia --perm EDIT     # 加协作者
//   node document-permission.mjs <documentId> --update guwenjia --perm READ  # 改协作者权限
//   node document-permission.mjs <documentId> --remove guwenjia              # 移除协作者
//
// ⚠️ 协作者 username 是登录名（拼音），不确定时先用 resolve-user.mjs 查证——加错人等于把文档给了不该看的人。
// ⚠️ 改/移除协作者会立刻踢掉对方正在进行的编辑会话；收紧为 WHITELIST_ONLY 会让名单外的人立刻看不到这篇文档。
// ⚠️ 除 --get 外，其余操作只有文档所有者或空间管理员能做。

const ACCESS_MODES = ['OPEN_EDIT', 'OPEN_READONLY', 'WHITELIST_ONLY'];
const PERMISSIONS = ['READ', 'EDIT'];

const USAGE = [
  '用法:',
  '  node document-permission.mjs <documentId> --get',
  `  node document-permission.mjs <documentId> --set-mode <${ACCESS_MODES.join('|')}>`,
  '  node document-permission.mjs <documentId> --list',
  '  node document-permission.mjs <documentId> --add <登录名> --perm READ|EDIT',
  '  node document-permission.mjs <documentId> --update <登录名> --perm READ|EDIT',
  '  node document-permission.mjs <documentId> --remove <登录名>',
].join('\n');

const args = parseArgs(process.argv);
const documentId = args._[0];

if (!documentId) {
  console.error(USAGE);
  process.exit(1);
}

/** 取 --flag 的值：既支持 --add guwenjia，也支持 --add 后面跟位置参数 */
function flagValue(flag, label) {
  const value = args[flag] === true ? args._[1] : args[flag];
  if (!value) {
    console.error(`错误: --${flag} 需要指定${label}`);
    process.exit(1);
  }
  return String(value);
}

function resolvePermission() {
  const perm = args.perm ? String(args.perm).toUpperCase() : '';
  if (!PERMISSIONS.includes(perm)) {
    console.error(`错误: 需要 --perm ${PERMISSIONS.join(' 或 ')}`);
    process.exit(1);
  }
  return perm;
}

if (args.get) {
  const data = await apiRequest('GET', `/document/${documentId}/permissions`);
  console.log(`文档:            ${documentId}`);
  console.log(`所有者:          ${data.owner}`);
  console.log(`访问模式:        ${data.accessMode}`);
  console.log(`我可读:          ${data.canRead ? '是' : '否'}`);
  console.log(`我可编辑:        ${data.canEdit ? '是' : '否'}`);
  console.log(`我可管理权限:    ${data.canManagePermission ? '是' : '否'}`);
  console.log(`URL:             ${getDocumentUrl(documentId)}`);
} else if (args['set-mode']) {
  const accessMode = String(args['set-mode']).toUpperCase();
  if (!ACCESS_MODES.includes(accessMode)) {
    console.error(`错误: accessMode 需为 ${ACCESS_MODES.join(' / ')} 之一`);
    process.exit(1);
  }
  if (accessMode === 'WHITELIST_ONLY') {
    console.log('⚠️  收紧为白名单模式后，不在协作者名单内的人将立刻无法访问这篇文档。\n');
  }

  await apiRequest('PUT', `/document/${documentId}/access-mode`, { accessMode });
  console.log(`访问模式已更新为 ${accessMode}`);
  console.log(`URL: ${getDocumentUrl(documentId)}`);
} else if (args.list) {
  const collaborators = await apiRequest('GET', `/document/${documentId}/collaborators`);
  console.log(`文档 ${documentId} 共 ${collaborators.length} 位协作者（不含所有者）:\n`);
  for (const c of collaborators) {
    console.log(`  ${c.username}  ${c.permission}`);
  }
} else if (args.add) {
  const username = flagValue('add', '协作者登录名');
  const permission = resolvePermission();

  const data = await apiRequest('POST', `/document/${documentId}/collaborators`, { username, permission });
  console.log(`已添加协作者: ${data.username}  ${data.permission}`);
} else if (args.update) {
  const username = flagValue('update', '协作者登录名');
  const permission = resolvePermission();

  const data = await apiRequest('PUT', `/document/${documentId}/collaborators/${username}`, { permission });
  console.log(`已更新协作者权限: ${data.username}  ${data.permission}`);
  console.log('（对方正在进行的编辑会话已被断开）');
} else if (args.remove) {
  const username = flagValue('remove', '协作者登录名');

  await apiRequest('DELETE', `/document/${documentId}/collaborators/${username}`);
  console.log(`已移除协作者: ${username}`);
  console.log('（对方正在进行的编辑会话已被断开）');
} else {
  console.error(USAGE);
  process.exit(1);
}
