# 文档里的图片

知了文档正文里的图片，最终需要是**可公网访问的绝对 URL**。直接上传 `.html`/`.htm` 单文件时，`img[src]` 中的 `data:image/...;base64,...` 会由服务端自动提取、转存 Boss 并替换为公网 URL，不要自己解码或上传这些内嵌图。相对路径 / 本地路径 / 内网私域地址仍需要上传并替换（相对路径会被解析到 aistudio 域名，本地/私域地址在别人电脑上无法访问）。

## 上传图片拿公网 URL

```bash
node {baseDir}/scripts/upload-image.mjs /path/to/image.png
```

支持 jpg / jpeg / png / gif / webp，最大 5MB。输出里的 `URL`（形如 `https://aistudio.bilibili.co/api/v1/boss/proxy/copilot/xxx.png`）就是可直接写进文档的地址，用 `![图片](url)` 插入。

## 场景一：把本地图片插进已有文档

1. `upload-image.mjs` 拿到公网 url；
2. 写进文档——插到文末用 `apply-document-edge.mjs`（免读全文）：

```bash
printf '![图片](https://aistudio.bilibili.co/api/v1/boss/proxy/copilot/xxx.png)' \
  | node {baseDir}/scripts/apply-document-edge.mjs doc_xxxxxxxxxx --append
```

插到**文档中间的指定位置**，则先 `get-lossless-markdown` 拿基准，再用补丁锚定插入点上一行、在其后 `+` 插入图片段落。

用户给的已经是公网 url（http/https 开头）时直接写进文档即可，不用再上传。

## 场景二：提交带图的 markdown 前，先迁移非公网图片

只要要 create / update / upload 的 markdown 正文里含下列任一种图片地址，**必须先把图转存到图床、把正文里的地址替换成返回的公网 URL，再提交文档**：

- **相对路径**：`/api/documents/kb-image/xxx.png`、`./img/a.png`、`../assets/b.jpg` 等不以 `http(s)://` 开头的
- **本地路径**：`/Users/xxx/a.png`、`C:\Users\xxx\a.png`、`file:///...`
- **内网 / 私域服务器**：`http://10.x.x.x...`、`http://localhost...`、公司内网 IP / 内网域名上的图

已经是公网可访问的绝对 URL（boss 图床、公网图床、CDN）直接保留，不用动。拿不准某个内网域名是否公网可达时，倾向于迁移。

**适用范围**：`.md` / `.txt` / `.html` 中的相对、本地或内网图片需要这一步；HTML Base64 内嵌图例外。`.pdf` / `.doc` / `.docx` / `.ppt` / `.pptx` / `.zip` 由服务端解析，不需要。HTML 连同多个本地图片、CSS 或 JS 组成完整页面时，优先保留相对目录结构并打包 ZIP 上传，不要逐个改链接。

**迁移流程（对每一张需迁移的图）：**

1. **取到图片字节**：本地路径直接读文件；相对路径按文档来源域名补全成完整 URL 再下载（例：源文档来自 `http://10.23.28.27:3000` 的，`/api/documents/kb-image/x.png` → `http://10.23.28.27:3000/api/documents/kb-image/x.png`）；内网 URL 直接下载。下载到本地临时文件。
2. `upload-image.mjs` 传到图床拿公网 URL。
3. **把正文里这张图的原地址整段替换成返回的 URL**，全文同一地址全部替换。
4. 全部替换完、正文里已无相对/本地/私域图片地址后，再提交文档。

**批量注意：**

- 图多时**先去重**（同一地址只下载+上传一次，建一张「原地址 → 图床 URL」映射表，再全文替换），别对重复地址反复传。
- 图床**限频每秒最多 6 次**上传。图多（十几张以上）时循环里加节流（每次间隔 ~200–400ms），并对偶发 `code=429 请求过于频繁` 的失败项重试，别一把并发打上去。
- 迁移是一次性批处理：可写个临时 Node 脚本跑「下载→上传→替换」，跑完确认正文 0 个残留相对/本地/私域地址，再提交文档。
- 若个别图取不到（源地址已失效等），保留原地址并**明确告诉用户哪几张没迁移成功**，不要静默丢图。
