---
name: zhiliao
description: 知了文档平台 (aistudio.bilibili.co) 工具。读取、上传和管理 Markdown/PDF/Word/HTML/ZIP 文档，从 URL 导入网页，无损补丁编辑，管理权限与评论，语义搜索知识库。Use when the user gives an aistudio.bilibili.co link (e.g. .../wiki/doc_xxx, .../wiki/sp_xxx, .../wiki/fd_xxx, or the older .../space/doc/doc_xxx and .../share/doc_xxx), or mentions 打开/读取/查看知了文档、知了、aistudio.bilibili.co、文档提交、文档上传、网页上传、URL 导入、增量编辑、文档权限、文档评论、知识库搜索、zhiliao。一旦出现知了文档链接或需要读取知了文档内容，用本 skill 的脚本，不要用网页抓取(WebFetch)。
homepage: https://aistudio.bilibili.co
metadata:
  {
    'clawdbot':
      {
        'emoji': '📝',
        'requires': { 'bins': ['node'], 'env': ['ZHILIAO_API_KEY'] },
        'primaryEnv': 'ZHILIAO_API_KEY',
      },
  }
version: 1.5.4
---

# 知了文档平台 (zhiliao)

B 站内网文档平台。文档平台上人能做的事，这里都能做：读写文档、无损编辑、管权限、看评论、搜知识库。

**本会话首次激活时跑一次版本自检**（整个会话只跑这一次）：`node {baseDir}/scripts/check-version.mjs`。它会比对本地与服务端版本，落后时打印升级指引，请**原样转达给用户**。网络失败会静默跳过，不阻断任何操作。

## 该用哪个脚本

| 你要做的事                                    | 用这个                                           |
| --------------------------------------------- | ------------------------------------------------ |
| 改文档局部（改措辞/重写某节/补删一段/改表格） | `get-lossless-markdown` + `apply-document-patch` |
| 只往文档开头或结尾加内容                      | `apply-document-edge`（免读全文）                |
| 只改标题 / 标签                               | `update-metadata`                                |
| 整篇重写、内容几乎全换                        | `update-document`（**最后手段**，见下）          |
| 新建文档                                      | `create-document`                                |
| 传本地文件创建/更新文档（含 HTML/ZIP 网页）   | `upload-document`                                |
| 从 URL 创建/更新引用文档、查询导入状态        | `import-url`、`get-web-import-status`            |
| 看文档正文                                    | `get-document`                                   |
| 找文档 / 找资料                               | `search-knowledge`                               |
| 管权限、加协作者                              | `document-permission`                            |
| 看/发评论                                     | `document-comments`、`collaboration-events`      |
| 插图片、@某人                                 | `upload-image`、`resolve-user`                   |

**改已有文档默认走补丁编辑。** `update-document` 是整篇覆盖：重排所有块，**丢掉划词评论锚点、文字颜色、表格列宽**，且不可恢复。只有「整篇重写 / 内容几乎全换 / 从本地文件整体覆盖」才用它。

## 脚本清单

所有脚本都在 `{baseDir}/scripts/` 下，用 `node {baseDir}/scripts/xxx.mjs` 调用。文档 ID 形如 `doc_xxx`。

**空间与目录**

```bash
node {baseDir}/scripts/list-spaces.mjs                     # 可访问的空间
node {baseDir}/scripts/list-folders.mjs sp_xxx             # 空间下的目录（name 为 "/" 的是根目录）
node {baseDir}/scripts/list-documents.mjs fd_xxx           # 目录下的文档
node {baseDir}/scripts/create-folder.mjs --name "名称" [--space-id sp_xxx] [--parent-id fd_xxx]
```

**读文档**

```bash
node {baseDir}/scripts/get-document.mjs doc_xxx            # 看正文（给人读）
node {baseDir}/scripts/get-document.mjs --title "标题"     # 语义搜索定位，会打印命中的标题供核对
node {baseDir}/scripts/get-lossless-markdown.mjs doc_xxx   # 拿编辑基准（带 HTML 标签，供写补丁）
node {baseDir}/scripts/search-knowledge.mjs "关键词" [--limit 5] [--tags "a,b"] [--space-id "sp_1,sp_2"] [--acl "team-tag"] [--source doc --source-id doc_xxx]
node {baseDir}/scripts/get-knowledge-source.mjs --source doc --source-id doc_xxx   # 搜索结果的完整正文
```

**写文档**

```bash
node {baseDir}/scripts/create-document.mjs --title "标题" --content "# 内容" [--space-id sp_xxx] [--folder-id fd_xxx]
cat doc.md | node {baseDir}/scripts/create-document.mjs --title "标题"

# 补丁编辑（改已有文档的默认方式）：先读基准，再提交补丁
printf '*** Begin Patch\n@@\n <上一行做锚>\n-旧的整行\n+新的整行\n*** End Patch\n' \
  | node {baseDir}/scripts/apply-document-patch.mjs doc_xxx

# 纯头尾追加（免读全文）
printf '## 新章节\n\n正文。' | node {baseDir}/scripts/apply-document-edge.mjs doc_xxx --append
printf '# 置顶公告'          | node {baseDir}/scripts/apply-document-edge.mjs doc_xxx --prepend

node {baseDir}/scripts/update-metadata.mjs doc_xxx --title "新标题" [--tags "a,b"]
node {baseDir}/scripts/update-document.mjs doc_xxx --content "全新正文"   # 整篇覆盖，慎用
node {baseDir}/scripts/delete-document.mjs doc_xxx
```

`update-document` 的 `--content` 有三态，别搞混：**不传 = 完全不动正文**（此时只改标题，等价于 update-metadata 但会重排全文，所以还是该用 update-metadata）；**传 `--content ""` = 清空正文**；传内容 = 整篇覆盖。`--title` / `--content` 至少给一个。

**上传本地文件**

```bash
node {baseDir}/scripts/upload-document.mjs /path/doc.md [--title "标题"] [--space-id sp_xxx] [--folder-id fd_xxx]
node {baseDir}/scripts/upload-document.mjs /path/report.pdf --space-id sp_xxx --folder-id fd_xxx [--tags "a,b"]
node {baseDir}/scripts/upload-document.mjs /path/page.html [--tags "a,b"] # .html / .htm / .zip 静态站点
node {baseDir}/scripts/upload-document.mjs /path/page-v2.htm --document-id doc_xxx
```

- `.md` 等文本走创建/整篇覆盖；`.pdf`/`.doc`/`.docx`/`.ppt`/`.pptx` 仅支持创建；`.html`/`.htm`/`.zip` 走网页托管上传。直接上传 HTML/HTM 单文件时，`img[src]` 内嵌 Base64 图片会由服务端自动转存图床
- 单文件上限 20MB
- 更新必须显式传 `--document-id doc_xxx`；不按标题猜测目标。HTML/HTM 可互相更新，ZIP 只能更新 ZIP；文件上传网页与 URL 引用文档不能交叉更新
- 网页更新只替换托管资源并保留原标题/标签；网页标题由页面或文件解析，服务端忽略 `--title`
- **纯文本类上传前先处理无法随文件提交的图片**（见下）：HTML Base64 内嵌图例外，由服务端自动处理

**从 URL 导入网页**

```bash
node {baseDir}/scripts/import-url.mjs "https://example.com/page" [--title "标题"] [--space-id sp_xxx] [--folder-id fd_xxx] [--tags "a,b"]
node {baseDir}/scripts/import-url.mjs "https://example.com/page-v2" --document-id doc_xxx
node {baseDir}/scripts/get-web-import-status.mjs <taskId>
```

URL 导入是异步任务，仅支持 HTTPS。创建时可设标题/标签；更新只更换 URL 并重新抓取，保留原标题/标签。拿到 task ID 后查询到 `completed` 或 `failed`。

**权限与协作者**

```bash
node {baseDir}/scripts/document-permission.mjs doc_xxx --get                         # 访问模式 + 我的权限
node {baseDir}/scripts/document-permission.mjs doc_xxx --set-mode OPEN_READONLY      # OPEN_EDIT / OPEN_READONLY / WHITELIST_ONLY
node {baseDir}/scripts/document-permission.mjs doc_xxx --list                        # 协作者名单
node {baseDir}/scripts/document-permission.mjs doc_xxx --add guwenjia --perm EDIT
node {baseDir}/scripts/document-permission.mjs doc_xxx --update guwenjia --perm READ
node {baseDir}/scripts/document-permission.mjs doc_xxx --remove guwenjia
```

协作者用登录名（拼音），不确定先 `resolve-user.mjs` 查证。改/移除协作者会立刻断开对方的编辑会话；收紧为 `WHITELIST_ONLY` 会让名单外的人立刻看不到文档——这类收紧动作**先跟用户确认**。除 `--get` 外都需要文档所有者或空间管理员身份。

**评论**

```bash
node {baseDir}/scripts/collaboration-events.mjs [--unread] [--types comment.mentioned]   # 跨文档：谁评论/回复/@了我
node {baseDir}/scripts/document-comments.mjs doc_xxx --list                              # 某篇文档的评论
node {baseDir}/scripts/document-comments.mjs doc_xxx --create --text "内容" [--mentions "guwenjia"]   # 文档级评论
node {baseDir}/scripts/document-comments.mjs doc_xxx --create --text "内容" --quote "被评论的那一行原文"  # 划词评论
node {baseDir}/scripts/document-comments.mjs doc_xxx --reply <commentId> --text "内容"
node {baseDir}/scripts/document-comments.mjs doc_xxx --update <commentId> --text "内容"
node {baseDir}/scripts/document-comments.mjs doc_xxx --delete <commentId>
```

评论会以用户身份公开发出、`--mentions` 会真实推送通知，**发之前确认用户确实要留言**。只能改/删自己创建的评论。

**针对某句话提意见就用 `--quote`**，评论会像人一样锚定在正文那段话上（编辑器里是划词高亮），比笼统的文档级评论有用得多。`--quote` 必须是文档里的**一整行原文照抄**：先 `get-lossless-markdown` 拿正文，剥掉 markdown 语法（`**粗体**` → `粗体`、`[文字](url)` → `文字`）后原样复制，不要改写、不要跨行拼接、也不要只取其中一小段——短片段极易在全文撞到多处而被拒。找不到或有多处都会报错，错误信息里会给出文档中最接近的那一行，照它调整后重试。

## 补丁编辑铁律

1. **先读最新基准**：写补丁前必须 `get-lossless-markdown` 拿当前内容，不能凭记忆或旧快照。文档改过之后要再改，必须重新读一次。
2. **逐字一致**：补丁里的上下文行和删除行必须与读到的内容完全一致（含 HTML 标签、缩进空格、标点）。
3. **默认带 1 行前置上下文**定位，报「匹配到多处」再加到 2–3 行。
4. **报错就按提示修锚点重试，不要退回 `update-document` 绕过。** 并发冲突（提示「被其他协作者改动」）要重新读基准、重写补丁，别原样重试。

补丁格式、操作符细则、表格编辑、长文档按章节取基准、各类报错处置 → **读 `{baseDir}/references/patch-format.md`**。

## 其它约束

- **图片必须是公网 URL**：直接上传 HTML/HTM 单文件时，`img[src]` 中的 Base64 内嵌图会自动转存；本地 / 相对路径 / 内网地址仍需先用 `upload-image.mjs` 传到图床再替换。完整页面含多个本地资源时优先按原目录结构打包 ZIP。完整迁移流程、批量去重与限频 → `{baseDir}/references/images.md`。
- **@提及的 id/label 绝不能编**：`id` 是登录名（拼音）、`label` 固定是「昵称 (登录名)」，编错就是 @ 错人且会真实推送通知。用 `resolve-user.mjs` 查证。文字颜色、`<mention>`、`<comment>` 的写法 → `{baseDir}/references/styling.md`。
- **写操作只认 `doc_xxx`**：`update-document` / `delete-document` / `update-metadata` / `apply-document-*` 都不接受按标题模糊定位——只知道标题就先 `get-document.mjs --title` 或 `search-knowledge.mjs` 查到确切 ID 并核对。
- **从链接取 ID**：站内地址现在统一是 `https://aistudio.bilibili.co/wiki/{id}`，文档 `doc_xxx`、空间 `sp_xxx`、目录 `fd_xxx` 共用这一条路径，取出 `/wiki/` 后面那一段就是 ID（拿到 `sp_` 就用 `list-folders.mjs`，拿到 `fd_` 就用 `list-documents.mjs`）。旧链接同样只需取出 `doc_` / `fd_` / `sp_` 开头的那段：`.../space/doc/doc_xxx`、`.../space/folder/fd_xxx`、`.../space/{sp_xxx}` 是旧版客户端的地址（新版已经打不开），`.../share/doc_xxx` 是文档分享页（仍然有效）。只要用户给了知了链接，就用本 skill 读，**不要用 WebFetch**——知了文档是登录后客户端渲染的，抓不到正文。
- **把链接给回用户**：写完/查完之后，脚本打印的 `URL:` 那一行已经是新版 `/wiki/` 地址，直接转达即可。空间和目录没有脚本打印链接，需要时自己按 `https://aistudio.bilibili.co/wiki/{sp_xxx|fd_xxx}` 拼。ID 只能用脚本真实返回过的，别凭印象编——编出来的必然是死链。用户没要求就**不要**为了把正文里的旧链接换成新的去改文档：那是一次没人要的改动，还会撞掉补丁锚点。
- **知识库同步是异步的**（embedding 队列），刚提交的内容搜索结果可能有几秒延迟。

## 上传时没指定空间 / 目录

用户没说传到哪里时：`list-spaces.mjs` 拿空间列表 → 用 AskUserQuestion 让用户选 → `list-folders.mjs <spaceId>` 拿目录 → 让用户选目录 → 带 `--space-id` / `--folder-id` 提交。

用户在 `config.json` 里配了 `defaultSpaceId` / `defaultFolderId` 则直接用；用户在请求里已明说「传到 XX 空间的 XX 目录」就直接传参，不必再问。

## API Key

优先级：`<cwd>/zhiliao_docs/apikey` 文件 > `ZHILIAO_API_KEY` 环境变量 > `{baseDir}/data/config.json` 的 `apiKey`。

脚本报「未配置有效的知了 API Key」或 401 时：引导用户在 `~/.claude/settings.json` 的 `env` 里加 `ZHILIAO_API_KEY`，并提示**配置完需重启 Claude Code 会话**才生效（settings.json 的 env 在会话启动时读入）。**不要替用户写入 key**。Key 形如 `aist_xxx`，向 aistudio.bilibili.co 平台管理员申请。

`config.json` 还可配 `baseUrl`、`defaultSpaceId`、`defaultFolderId`（默认上传位置）。
