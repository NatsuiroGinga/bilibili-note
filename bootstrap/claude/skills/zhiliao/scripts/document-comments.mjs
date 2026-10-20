import { apiRequest, parseArgs, getDocumentUrl } from './utils.mjs';

// 文档评论：读 / 发 / 回复 / 改 / 删。
//
// 两种评论形态，靠 --quote 区分：
//   带 --quote → **划词评论**，锚定在正文的那段话上（编辑器里显示为高亮），针对某句话提意见用它
//   不带      → 文档级评论，不绑定位置，适合对全文的总体意见
//
// 评论正文是 ProseMirror 富文本 JSON，不是纯文本。最简形态：
//   {"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"评论正文"}]}]}
// 为了好用，--text 会自动包成上面这个结构；要发富文本（多段落、加粗等）就用 --content 传完整 JSON。
//
// 用法：
//   node document-comments.mjs <documentId> --list [--type document|inline] [--page 1] [--page-size 50]
//   node document-comments.mjs <documentId> --create --text "说点什么" [--quote "被评论的原文"] [--mentions "guwenjia,mengna02"]
//   node document-comments.mjs <documentId> --reply <commentId> --text "回复内容" [--mentions "..."]
//   node document-comments.mjs <documentId> --update <commentId> --text "改后的内容"
//   node document-comments.mjs <documentId> --delete <commentId>
//
// ⚠️ --quote 必须是文档里的**一整行原文照抄**：先 get-lossless-markdown 拿正文，剥掉 markdown
//    语法（`**粗体**` → `粗体`，`[文字](url)` → `文字`）后原样复制，不要自己改写、不要跨行拼接。
//    它还必须在全文唯一 —— 太短容易撞重复。找不到或有多处都会报错，错误信息里会给出文档中最接近
//    的那一行，照它调整后重试。
// ⚠️ mentions 会真实推送通知给对方，登录名不确定时先用 resolve-user.mjs 查证，不要编。
// ⚠️ 只能改/删自己创建的评论。

const USAGE = [
  '用法:',
  '  node document-comments.mjs <documentId> --list [--type document|inline] [--page 1] [--page-size 50]',
  '  node document-comments.mjs <documentId> --create --text "内容" [--quote "被评论的原文"] [--mentions "登录名1,登录名2"]',
  '  node document-comments.mjs <documentId> --reply <commentId> --text "内容"',
  '  node document-comments.mjs <documentId> --update <commentId> --text "内容"',
  '  node document-comments.mjs <documentId> --delete <commentId>',
  '',
  '--text 是纯文本快捷写法；要发富文本用 --content \'<ProseMirror JSON>\'',
  '--quote 传文档里的一整行原文即发划词评论（锚定到正文那段话），不传则是文档级评论',
].join('\n');

const args = parseArgs(process.argv);
const documentId = args._[0];

if (!documentId) {
  console.error(USAGE);
  process.exit(1);
}

/** 把 --text / --content 归一成 ProseMirror JSON */
function resolveContent() {
  if (args.content) {
    try {
      return JSON.parse(args.content);
    } catch (err) {
      console.error(`错误: --content 不是合法 JSON（${err.message}）`);
      console.error('提示: 纯文本评论直接用 --text "内容" 即可，无需自己拼 JSON');
      process.exit(1);
    }
  }
  if (typeof args.text === 'string') {
    return {
      type: 'doc',
      content: [{ type: 'paragraph', content: [{ type: 'text', text: args.text }] }],
    };
  }
  console.error('错误: 需要 --text "内容" 或 --content \'<ProseMirror JSON>\'');
  process.exit(1);
}

/** --mentions "a,b" → [{username:'a'},{username:'b'}] */
function resolveMentions() {
  if (typeof args.mentions !== 'string') return undefined;
  const list = args.mentions.split(',').map((s) => s.trim()).filter(Boolean);
  return list.length ? list.map((username) => ({ username })) : undefined;
}

/** 从 ProseMirror JSON 里抽纯文本，仅用于列表展示 */
function toPlainText(node) {
  if (!node || typeof node !== 'object') return '';
  if (node.type === 'text') return node.text || '';
  return (node.content || []).map(toPlainText).join('');
}

function printComment(comment, indent = '') {
  const text = toPlainText(comment.contentJson).replace(/\n/g, ' ');
  console.log(`${indent}[${comment.id}] ${comment.createdBy}  ${comment.ctime || ''}`);
  console.log(`${indent}  ${text || '(空)'}`);
  if (comment.markId) console.log(`${indent}  划词锚点: ${comment.markId}`);
  if (comment.quotedText) console.log(`${indent}  引用原文: ${comment.quotedText}`);
  for (const reply of comment.replies || []) printComment(reply, `${indent}    `);
}

if (args.list) {
  const params = new URLSearchParams();
  if (args.type) params.set('commentType', String(args.type));
  if (args.page) params.set('page', String(args.page));
  if (args['page-size']) params.set('pageSize', String(args['page-size']));
  const qs = params.toString();

  const data = await apiRequest('GET', `/document/${documentId}/comments${qs ? `?${qs}` : ''}`);
  const items = data.items || [];
  console.log(`文档 ${documentId} 共 ${data.total ?? items.length} 条评论（本页 ${items.length} 条）:\n`);
  for (const comment of items) {
    printComment(comment);
    console.log('');
  }
  console.log(`URL: ${getDocumentUrl(documentId)}`);
} else if (args.create) {
  const body = { content: resolveContent() };
  const mentions = resolveMentions();
  if (mentions) body.mentions = mentions;
  if (typeof args.quote === 'string' && args.quote) body.quotedText = args.quote;

  const data = await apiRequest('POST', `/document/${documentId}/comments`, body);
  const comment = data.comment || {};
  console.log(`${comment.markId ? '划词评论' : '评论'}已发布: ${comment.id || ''}`);
  if (comment.markId) {
    console.log(`  锚定原文: ${comment.quotedText || ''}`);
    // 多段说明引文中间夹了链接 / @提及 —— 那几截承载不了高亮，会断开，与真人划词一致
    if ((comment.segments || []).length > 1) {
      console.log(`  注意: 引文中间有链接或 @提及，高亮会分成 ${comment.segments.length} 段`);
    }
  }
  if (comment.deduplicated) console.log('  （已存在同样的评论，返回的是原来那条，未重复创建）');
  console.log(`URL: ${getDocumentUrl(documentId)}`);
} else if (args.reply) {
  const commentId = args.reply === true ? args._[1] : String(args.reply);
  if (!commentId) {
    console.error('错误: --reply 需要指定被回复的 commentId（用 --list 查看）');
    process.exit(1);
  }
  const body = { content: resolveContent() };
  const mentions = resolveMentions();
  if (mentions) body.mentions = mentions;

  const data = await apiRequest('POST', `/document/${documentId}/comments/${commentId}/replies`, body);
  console.log(`回复已发布: ${data?.id || ''}`);
  console.log(`URL: ${getDocumentUrl(documentId)}`);
} else if (args.update) {
  const commentId = args.update === true ? args._[1] : String(args.update);
  if (!commentId) {
    console.error('错误: --update 需要指定 commentId（用 --list 查看）');
    process.exit(1);
  }
  const body = { content: resolveContent() };
  const mentions = resolveMentions();
  if (mentions) body.mentions = mentions;

  await apiRequest('POST', `/document/${documentId}/comments/${commentId}/update`, body);
  console.log(`评论已更新: ${commentId}`);
} else if (args.delete) {
  const commentId = args.delete === true ? args._[1] : String(args.delete);
  if (!commentId) {
    console.error('错误: --delete 需要指定 commentId（用 --list 查看）');
    process.exit(1);
  }

  await apiRequest('DELETE', `/document/${documentId}/comments/${commentId}`);
  console.log(`评论已删除: ${commentId}`);
} else {
  console.error(USAGE);
  process.exit(1);
}
