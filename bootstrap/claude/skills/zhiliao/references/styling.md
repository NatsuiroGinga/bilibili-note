# 文字颜色、@提及、划词评论

无损 markdown 里这几样都有固定写法，写补丁或用 `apply-document-edge.mjs` 插入内容时照此办理。

## 文字颜色

彩色文字用**原生 CSS `style`** 承载（正文和表格里写法完全一致）：

```html
<span style="color: var(--Re5);">红色文字</span>
<span style="background: linear-gradient(transparent 50%, var(--Ye2) 50%);">黄色高亮</span>
<span style="background: linear-gradient(transparent 50%, var(--Ye2) 50%); color: var(--Re5);">底色+字色</span>
```

- **文字色**用 `color: var(--XXX);`；**背景色/高亮**用固定的半高渐变写法 `background: linear-gradient(transparent 50%, var(--XXX) 50%);`（照抄这串，只换令牌）。两者可写在同一个 `style` 里、用 `; ` 分隔。
- **改已有带色文字**：照抄原 `style` 不动、只改文字部分。**主动上色**：从下表选一个令牌套进模板。
- **别用** `<span data-ts='...'>` 那种旧写法（已废弃，服务端不再输出，也不要手写）。
- 只需颜色令牌（`var(--Re5)`），不必写 hex——前端按令牌解析真实颜色。

常用颜色令牌：

| 用途                                | 令牌  | 颜色   |
| ----------------------------------- | ----- | ------ |
| 文字-黑（正文默认，通常无需显式设） | `Ga9` | 近黑   |
| 文字-灰                             | `Ga5` | 中灰   |
| 文字-红（警示）                     | `Re5` | 红     |
| 文字-橙                             | `Or5` | 橙     |
| 文字-黄                             | `Ly5` | 亮黄   |
| 文字-绿                             | `Gr5` | 绿     |
| 文字-蓝（链接常用）                 | `Bl5` | 蓝     |
| 文字-紫                             | `Pu5` | 紫     |
| 背景-黄（高亮常用）                 | `Ye2` | 浅黄底 |
| 背景-粉                             | `Pi2` | 浅粉底 |
| 背景-绿                             | `Gr2` | 浅绿底 |
| 背景-蓝                             | `Bl2` | 浅蓝底 |

深浅档：文字色把末位数字调大更深、调小更浅（如 `Re3` 浅红 / `Re5` 中红 / `Re7` 深红），青 `Cy`/绿 `Gr`/黄 `Ly`/橙 `Or`/红 `Re`/紫 `Pu`/蓝 `Bl` 同理。拿不准就用中档（末位 5）。

## @提及（mention）

自描述标签 `<mention data-attrs='{...}'/>`（自闭合，单引号包 JSON）：

```html
<mention data-attrs='{"id":"mengna02","label":"阿菲 (mengna02)","mentionSuggestionChar":"@","notificationId":"..."}' />
```

- **移动 / 保留已有提及**：照抄原文那段 `<mention data-attrs='...'/>` 整体，`notificationId` 等原样不动。
- **新建一次提及**：插入 `<mention data-attrs='{"id":"<登录名>","label":"<昵称> (<登录名>)","mentionSuggestionChar":"@"}'/>` 即可，**`notificationId` 不用写**——服务端会为新提及自动生成。
- ⚠️ **id/label 必须真实，绝不能编**：`id` 是被提及人的登录名（拼音，如 `guwenjia`）、`label` 固定是「昵称 (登录名)」。编错了就是 @ 错人，而且**会真的给对方推送通知，撤不回来**。

只知道其中一半时用 `resolve-user.mjs` 查（登录名、姓名拼音、昵称都能模糊匹配；**OA 没有中文名**，不能按中文名查）：

```bash
node {baseDir}/scripts/resolve-user.mjs guwenjia    # 只知登录名 → 补出昵称
node {baseDir}/scripts/resolve-user.mjs Zerooo      # 只知昵称   → 补出登录名
```

直接打印可粘贴的 `<mention .../>` 标签。两种情况**都不要自己拿主意**：匹配到多人 → 把候选列表给用户挑，拿到确切登录名再查一次；查不到 → 回去问用户要登录名（已离职的人不会出现在结果里）。

示例——在某段末尾 @某人跟进：

```
*** Begin Patch
@@
 这是需要跟进的事项。
-请相关同学处理。
+请 <mention data-attrs='{"id":"mengna02","label":"阿菲 (mengna02)","mentionSuggestionChar":"@"}'/> 跟进。
*** End Patch
```

## 划词评论（comment）

包裹文字的自描述标签（单引号包 JSON，正文和表格写法一致）：

```html
<comment data-attrs='{"commentId":"comment-1786266815644-wei71fm5"}'>被评论的文字</comment>
```

- **改带评论的文字**：照抄整个 `<comment ...>...</comment>`、`commentId` 原样不动，只改标签内的文字。删除评论锚点则连标签一起删。
- ⚠️ `commentId` 关联评论线程，**别改、别编**。
- 要读写评论内容本身（发评论、回复、@人）用 `document-comments.mjs`，不通过补丁做。
- ⚠️ **不要自己拼 `<comment>` 标签来「加划词评论」** —— 手写的 commentId 没有对应的评论记录，编辑器里点开是空的。发划词评论用 `document-comments.mjs --create --quote "原文"`，锚点由服务端生成。
