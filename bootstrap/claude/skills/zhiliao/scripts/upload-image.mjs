import { readFileSync } from 'fs';
import { basename, extname } from 'path';
import { loadConfig } from './utils.mjs';

// 上传本地图片到知了图床，返回可直接写入文档 markdown 的完整 URL。
// 用法: node upload-image.mjs <本地图片路径>
//
// 典型场景：用户要把本地图片插入文档时——
//   1. 先用本脚本上传，拿到 url
//   2. 再用 apply-document-patch 以 ![图片](url) 把图片插入到目标位置
//
// 走 multipart/form-data（与 server /image/upload 一致），用 Node 内置 fetch + FormData。

const MIME_BY_EXT = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
};

const filePath = process.argv[2];

if (!filePath) {
  console.error('用法: node upload-image.mjs <本地图片路径>');
  console.error('支持格式: jpg / jpeg / png / gif / webp，最大 5MB');
  process.exit(1);
}

const ext = extname(filePath).toLowerCase();
const mime = MIME_BY_EXT[ext];
if (!mime) {
  console.error(`不支持的图片格式: ${ext || '(无扩展名)'}，仅支持 jpg/jpeg/png/gif/webp`);
  process.exit(1);
}

let buffer;
try {
  buffer = readFileSync(filePath);
} catch (err) {
  console.error(`读取文件失败: ${err.message}`);
  process.exit(1);
}

const { apiKey, baseUrl } = loadConfig();

const form = new FormData();
form.append('file', new Blob([buffer], { type: mime }), basename(filePath));

let response;
try {
  response = await fetch(`${baseUrl}/image/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
  });
} catch (err) {
  console.error(`网络错误: ${err.message}`);
  process.exit(1);
}

const raw = await response.text();
let json;
try {
  json = JSON.parse(raw);
} catch {
  console.error(`响应解析失败 (HTTP ${response.status}): ${raw.slice(0, 500)}`);
  process.exit(1);
}

if (json.code !== 0) {
  console.error(`上传失败: ${json.message || '未知错误'} (code=${json.code})`);
  process.exit(1);
}

const { url } = json.data;
console.log('图片上传成功');
console.log(`  URL:      ${url}`);
console.log(`\n可用以下 markdown 把图片插入文档（配合 apply-document-patch）:`);
console.log(`  ![图片](${url})`);
