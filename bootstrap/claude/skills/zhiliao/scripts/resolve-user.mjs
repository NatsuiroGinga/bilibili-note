import { apiRequest, parseArgs } from './utils.mjs';

// 按登录名 / 姓名拼音 / 昵称模糊查人，产出可直接粘贴的 <mention> 标签。
//
// 为什么需要这一步：mention 的 label 必须是「昵称 (登录名)」这种成对形式，而用户开口通常
// 只给得出其中一半——「帮我 @guwenjia」（只有登录名）或「@Zerooo」（只有昵称）。没有本脚本时，
// agent 只能去文档里翻现成的 mention 照抄，翻不到就只好凭空编一个。
// **编错的代价是 @ 错人，而且会真的推送通知，撤不回来。**
//
// 走知了 openapi 而不是直连公司 OA：OA 原始响应里有工号(workcode)、头像、上下级链、职级序列等一堆字段，
// 而 skill 跑在用户本机、拿到什么就等于往本地磁盘写什么。服务端已按白名单收敛到五个字段
// （login_id / nick_name / department_name / dept_id / manager），并滤掉已离职的人。
//
// 本脚本的原则是：宁可报错让 agent 回去问用户，也不猜。
//   - 登录名精确命中   → 直接选定
//   - 模糊只匹配到 1 人 → 选定
//   - 匹配到多人        → 列出全部并退出(1)，由用户挑，脚本不替他决定
//   - 一个都没有        → 退出(1)，别让 agent 把空结果当成「可以随便编」

const args = parseArgs(process.argv);

// 共用的 parseArgs 会把 `--json guwenjia` 里的 guwenjia 当作 --json 的取值吃掉，
// 关键词就丢了。这里把它捞回来，两种写法都能用。
const keyword =
  args._[0] || args.username || args.keyword || (typeof args.json === 'string' ? args.json : null);
const jsonMode = Boolean(args.json);

if (!keyword || keyword === true) {
  console.error('用法: node resolve-user.mjs <登录名|姓名拼音|昵称>');
  console.error('');
  console.error('示例:');
  console.error('  node resolve-user.mjs guwenjia         # 按登录名查，补出昵称');
  console.error('  node resolve-user.mjs Zerooo           # 按昵称查，补出登录名');
  console.error('  node resolve-user.mjs guwenjia --json  # 只输出 JSON，便于脚本消费');
  process.exit(1);
}

/** mention 的 label 固定是「昵称 (登录名)」，与在编辑器里手动 @ 出来的完全一致 */
const labelOf = (u) => `${u.nick_name} (${u.login_id})`;

const mentionTagOf = (u) =>
  `<mention data-attrs='${JSON.stringify({
    id: u.login_id,
    label: labelOf(u),
    mentionSuggestionChar: '@',
  })}'/>`;

const describe = (u) => `${labelOf(u)}${u.department_name ? `  ·  ${u.department_name}` : ''}`;

const users = await apiRequest('GET', `/oa/users/search?username=${encodeURIComponent(keyword)}`);

if (!users || users.length === 0) {
  console.error(`未找到匹配「${keyword}」的用户`);
  console.error('可换个说法重试：登录名（guwenjia）、姓名拼音、昵称（Zerooo）都支持模糊匹配');
  console.error('注意已离职的人不会出现在结果里');
  console.error('⚠️ 查不到时不要自己编造 id/label，请回去向用户确认登录名');
  process.exit(1);
}

// 登录名精确命中优先：搜 "guwenjia" 可能同时带出 "guwenjia02" 这类前缀相同的人，
// 此时本人一定是那个 login_id 完全相等的，不该因为「匹配到多人」就去打扰用户。
const exact = users.filter((u) => u.login_id.toLowerCase() === String(keyword).trim().toLowerCase());
const candidates = exact.length > 0 ? exact : users;

if (candidates.length > 1) {
  console.error(`「${keyword}」匹配到 ${candidates.length} 人，无法确定是哪一位：`);
  for (const u of candidates) {
    console.error(`  ${u.login_id.padEnd(16)} ${describe(u)}`);
  }
  console.error('');
  console.error('请把候选列表给用户挑选，拿到确切登录名后再用登录名重新查一次：');
  console.error(`  node resolve-user.mjs ${candidates[0].login_id}`);
  console.error('⚠️ 不要自行挑一个——@ 错人会真的给对方发通知');
  process.exit(1);
}

const user = candidates[0];

// data-attrs 用单引号包 JSON，昵称里若真出现单引号会截断属性、导致标签解析错乱。
// 概率极低，但真发生时静默产出坏标签更难查，所以显式拦下。
if (labelOf(user).includes("'")) {
  console.error(`用户昵称含单引号，无法安全拼进 data-attrs：${labelOf(user)}`);
  console.error('请手工处理该 mention，或反馈给平台维护方');
  process.exit(1);
}

if (jsonMode) {
  console.log(JSON.stringify({ id: user.login_id, label: labelOf(user) }));
  process.exit(0);
}

console.log(`已确定: ${describe(user)}`);
if (users.length > 1) {
  console.log(`（同时还模糊匹配到 ${users.length - 1} 人，因登录名精确命中而选定上面这位）`);
}
console.log('');
console.log('可直接粘进补丁的 mention 标签：');
console.log(mentionTagOf(user));
console.log('');
console.log('提示：新建提及不要写 notificationId，服务端会自动生成（提及一次 = 一条新通知）');
