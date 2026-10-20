import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

// 跨文档的评论协作动态：回答「我今天在哪些文档收到新评论 / 谁回复了我 / 谁 @ 了我」。
// 只返回当前 API Key 账号仍有权访问的文档上的事件。
//
// 要看某一篇文档的完整评论内容，用 document-comments.mjs <documentId> --list。
//
// 用法：
//   node collaboration-events.mjs                                  # 最近的协作动态
//   node collaboration-events.mjs --unread                          # 只看未读
//   node collaboration-events.mjs --types comment.mentioned         # 只看 @ 我的
//   node collaboration-events.mjs --start 2026-08-12T00:00:00Z --end 2026-08-13T00:00:00Z
//   node collaboration-events.mjs --limit 20 --cursor 12345         # 翻页（cursor 取上次返回的 nextCursor）
//
// 事件类型：comment.created（新评论）/ comment.replied（回复）/ comment.mentioned（@ 我）/ comment.deleted（删除）
// 时间必须是 UTC ISO 8601，如 2026-08-12T16:00:00Z。

const args = parseArgs(process.argv);

const params = new URLSearchParams();
if (args.unread) params.set('isRead', 'false');
if (args.read) params.set('isRead', 'true');
if (args.types) params.set('eventTypes', String(args.types));
if (args.start) params.set('startTime', String(args.start));
if (args.end) params.set('endTime', String(args.end));
if (args.cursor) params.set('cursor', String(args.cursor));
if (args.limit) params.set('limit', String(args.limit));

const limit = Number(args.limit) || 50;
const qs = params.toString();
const events = (await apiRequest('GET', `/collaboration-events${qs ? `?${qs}` : ''}`)) || [];

console.log(`共 ${events.length} 条协作动态:\n`);
for (const event of events) {
  const read = event.isRead ? '已读' : '未读';
  console.log(`  [${event.eventType}] ${read}  ${event.ctime || ''}`);
  console.log(`    文档: ${event.docId}  ${getDocumentUrl(event.docId)}`);
  if (event.operator) console.log(`    操作人: ${event.operator}`);
  if (event.commentId) console.log(`    评论: ${event.commentId}`);
  console.log('');
}

if (events.length === 0) {
  console.log('（没有符合条件的协作动态）');
} else if (events.length >= limit) {
  // 服务端按事件 id 游标翻页，取本页最后一条的 id 继续拉下一页
  console.log(`可能还有更多，续拉下一页: --cursor ${events.at(-1).id}`);
}
