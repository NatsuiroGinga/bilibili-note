#!/usr/bin/env python3
"""
将 raw/papers 下的 PDF 批量导入 Zotero，并生成/更新 wiki 论文笔记。

- 优先使用 PDF 内置元数据补全。
- 再尝试 CrossRef（10. DOI）与 Semantic Scholar（DOI）补齐。
- 写入 zotero 的标签：博弈论、PINN、网络异常流量检测。
- 入库成功后生成结构化摘要笔记。
- 输出导入结果与元数据缺失清单。
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import socket
import ssl
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path("/Users/bilibili/personal/note")
RAW_DIR = ROOT / "raw" / "papers"
WIKI_DIR = ROOT / "wiki" / "papers"
REPORT_DIR = ROOT / ".Codex" / "docs"
ZOTERO_URL = "http://127.0.0.1:23119/connector/"
ZOTERO_VERSION_HEADER = "3"
SOCKET_TIMEOUT = 8
socket.setdefaulttimeout(SOCKET_TIMEOUT)

MANDATORY_TAGS = ["博弈论", "PINN", "网络异常流量检测", "类型/论文"]


@dataclass
class ImportRecord:
    pdf_path: Path
    title: str
    status: str
    zotero: str
    note: str
    missing: List[str]


@dataclass
class PdfMeta:
    title: Optional[str] = None
    authors: List[str] = None
    year: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    identifier: Optional[str] = None
    abstract: Optional[str] = None
    source: str = "PDF内置"
    fulltext: Optional[str] = None
    fulltext_source: Optional[str] = None

    def __post_init__(self):
        if self.authors is None:
            self.authors = []


def run_cmd(cmd: List[str], timeout: int = 20) -> Optional[str]:
    """运行命令并返回标准输出；失败返回 None。"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def normalize_filename(text: str) -> str:
    """把标题转成安全文件名。"""
    text = text.strip().replace("/", "-")
    text = re.sub(r"[\\\*:?\"<>|]", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .")
    return text if text else "untitled"


def clean_author(name: str) -> str:
    name = name.strip().strip(";")
    return re.sub(r"\s+", " ", name)


def parse_year(raw_year: str) -> Optional[str]:
    if not raw_year:
        return None
    m = re.search(r"(19|20)\d{2}", raw_year)
    return m.group(0) if m else raw_year.strip()


def parse_pdfinfo(path: Path) -> PdfMeta:
    """用 pdfinfo + pdfinfo -meta 提取可用元数据。"""
    meta = PdfMeta()
    out = run_cmd(["pdfinfo", str(path)])
    if out:
        rows = out.splitlines()
        for line in rows:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            value = value.strip()
            if key == "Title":
                meta.title = value
            elif key == "Author":
                meta.authors = [clean_author(x) for x in re.split(r";|,| and | 与 | & ", value) if x.strip()]
            elif key == "CreationDate":
                if not meta.year:
                    meta.year = parse_year(value)
            elif key == "ModDate":
                if not meta.year:
                    meta.year = parse_year(value)
            elif key == "Subject":
                if not meta.journal:
                    meta.journal = value
    out_meta = run_cmd(["pdfinfo", "-meta", str(path)])
    if out_meta:
        # 常见的 XML 区块里会包含 dc:identifier / dc:title / dc:creator
        try:
            root = ET.fromstring(out_meta)
        except Exception:
            root = None
        if root is not None:
            # 简单按标签名抓取，兼容大小写和命名空间写法
            for elem in root.iter():
                tag = elem.tag.lower()
                if "identifier" in tag and not meta.identifier:
                    val = (elem.text or "").strip()
                    if val:
                        meta.identifier = val
                        if meta.doi is None:
                            m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", val)
                            if m:
                                meta.doi = m.group(0)
                if "title" in tag and not meta.title:
                    if elem.text:
                        meta.title = elem.text.strip()
                if "creator" in tag:
                    if elem.text and elem.text.strip() and elem.text.strip() not in meta.authors:
                        meta.authors.append(clean_author(elem.text))
                if "publisher" in tag and not meta.journal:
                    if elem.text:
                        meta.journal = elem.text.strip()
    if not meta.title:
        meta.title = path.stem
    if not meta.year:
        meta.year = parse_year(str(path.stat().st_mtime))
    if meta.journal is None:
        meta.journal = ""
    if not meta.authors:
        meta.authors = []
    return meta


def extract_fulltext(path: Path) -> Optional[str]:
    """尝试抽取全文：优先 pdftotext，不可用则返回 None。"""
    if shutil.which("pdftotext"):
        txt = run_cmd(["pdftotext", "-layout", str(path), "-"])
        if txt:
            return txt
    # 兜底：strings 质量较差，仅作“有内容则保留”，为空则认为失败
    txt = run_cmd(["strings", "-n", "8", str(path)])
    return txt if txt else None


def split_sections(text: str) -> Dict[str, str]:
    """从全文/摘要中抽取结构化摘要五个字段。"""
    clean = re.sub(r"\s+", " ", text or "")
    if not clean:
        return {
            "research_purpose": "",
            "model_architecture": "",
            "datasets": "",
            "core_conclusion": "",
            "refs_points": "",
        }

    def first_sentence(block: str, n=2):
        sents = re.split(r"(?<=[。.!?])\s+", block)
        return "".join(sents[:n]).strip() if block else ""

    purpose = ""
    arch = ""
    datasets = ""
    conclusion = ""
    refs = ""

    # 研究目的：优先使用摘要中的“本文/本文提出”句子
    m = re.search(r"(本文|本文提出|本文研究|本研究)[:：]?(.*?)(?=\s*[。.!?])", clean)
    if m:
        purpose = (m.group(1) + m.group(2)).strip()

    # 模型架构：含模型/框架/网络字样的前两句
    m = re.search(r"(模型|框架|网络|architecture|model)(.?[\w\W]{0,180})(\。|。|\.|!|\?)", clean, re.IGNORECASE)
    if m:
        idx = clean.find(m.group(0))
        seg = clean[idx:idx + 220]
        arch = first_sentence(seg, 2)

    # 实验数据集：找 dataset/data/数据集
    m = re.search(r"(数据集|数据集为|dataset|Dataset)([\w\W]{0,180}?)(实验|results|results\s*show|结果表明)", clean, re.IGNORECASE)
    if m:
        datasets = first_sentence(m.group(0), 2)

    # 核心结论：找 conclusion/results/evaluating
    m = re.search(r"(结论|结论是|实验结果|results show|results indicate)([\w\W]{0,220}?)(\。|\.|!|\?)", clean, re.IGNORECASE)
    if m:
        conclusion = first_sentence(m.group(0), 2)

    # 参考文献要点：抓“参考文献/References”段前1000字符
    refs_index = clean.lower().find("参考文献")
    if refs_index < 0:
        refs_index = clean.lower().find("references")
    if refs_index >= 0:
        ref_snip = clean[refs_index: refs_index + 600]
        refs = "；".join([x.strip() for x in re.split(r"(?<=\])|\n", ref_snip) if x.strip()][:5])

    return {
        "research_purpose": purpose or "",
        "model_architecture": arch or "",
        "datasets": datasets or "",
        "core_conclusion": conclusion or "",
        "refs_points": refs or "",
    }


def identify_collection_key(collection_name: Optional[str], db_path: Optional[Path] = None) -> Optional[str]:
    """尝试从本地 Zotero 数据库查询 collection key；失败返回 None。"""
    if not collection_name:
        return None
    # 不在本机运行时不强制报错，后续仍可按当前Zotero保存位置导入
    if db_path and db_path.exists():
        esc = collection_name.replace("'", "''")
        sql = f"SELECT key FROM collections WHERE LOWER(name)=LOWER('{esc}') LIMIT 1;"
        out = run_cmd(["sqlite3", "-readonly", str(db_path), sql])
        if out:
            key = out.strip().splitlines()[0].strip()
            return key if key else None
    return None


def request_json(url: str, params: Optional[Dict[str, str]] = None, timeout: int = 20) -> Optional[dict]:
    """请求 JSON 接口，失败返回 None。"""
    if params:
        url = url + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "note-zotero-import/1.0 (+https://openai.com)")
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
                if resp.status != 200:
                    return None
                raw = resp.read()
                return json.loads(raw.decode("utf-8", errors="ignore"))
        except (ssl.SSLError, urllib.error.URLError, TimeoutError, OSError, ValueError):
            # 统一按失败处理，避免单条网络波动导致整批卡死
            continue
    return None


def enrich_metadata(meta: PdfMeta) -> PdfMeta:
    """按 CrossRef + Semantic Scholar 继续补齐 DOI、作者、年份、期刊、摘要。"""
    if not meta.doi:
        # 尝试从 identifier 抽 DOI 再去交叉源取信息
        if meta.identifier:
            m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", meta.identifier)
            if m:
                meta.doi = m.group(0)

    if meta.doi:
        # 1) 用 DOI 从 CrossRef 查询
        doi_enc = urllib.parse.quote(meta.doi)
        cross = request_json(f"https://api.crossref.org/works/{doi_enc}")
        if cross and isinstance(cross, dict):
            msg = cross.get("message", {})
            if not meta.title and msg.get("title"):
                meta.title = msg.get("title", [""])[0] if isinstance(msg.get("title"), list) else msg.get("title")
            if not meta.journal:
                meta.journal = msg.get("container-title", [""])[0] if isinstance(msg.get("container-title"), list) else msg.get("container-title", "")
            if not meta.year:
                y = msg.get("issued", {}).get("date-parts", [[None]])[0][0]
                meta.year = str(y) if y else None
            if not meta.authors:
                meta.authors = []
                for a in msg.get("author", []) or []:
                    family = a.get("family", "")
                    given = a.get("given", "")
                    name = (f"{family}{' ' + given if given else ''}").strip() if family else (given or "")
                    if name:
                        meta.authors.append(clean_author(name))
            if not meta.abstract:
                abs_text = msg.get("abstract")
                if abs_text:
                    meta.abstract = re.sub(r"<[^>]+>", "", abs_text).strip()
                    meta.source = "CrossRef"
            return meta

        # 2) 用 DOI 查 Semantic Scholar
        s2 = request_json(
            f"https://api.semanticscholar.org/graph/v1/paper/{doi_enc}",
            params={"fields": "title,year,abstract,venue,authors"},
        )
        if s2 and isinstance(s2, dict):
            meta.title = meta.title or s2.get("title")
            if not meta.year:
                meta.year = str(s2.get("year")) if s2.get("year") else None
            if not meta.journal:
                meta.journal = s2.get("venue") or meta.journal
            if not meta.authors:
                meta.authors = [a.get("name", "") for a in (s2.get("authors") or []) if a.get("name")]
            if not meta.abstract:
                abs_text = s2.get("abstract")
                if abs_text:
                    meta.abstract = abs_text.strip()
                    meta.source = "Semantic Scholar"
            return meta

    # 最后尝试关键词检索 CrossRef（无 DOI）
    q = meta.title or ""
    if q:
        cands = request_json("https://api.crossref.org/works", params={"query.title": q[:250], "rows": 1})
        if cands and isinstance(cands, dict):
            msg = cands.get("message", {})
            items = msg.get("items") or []
            if items:
                item = items[0]
                if not meta.title:
                    meta.title = item.get("title", [""])[0] if isinstance(item.get("title"), list) else item.get("title")
                if not meta.journal:
                    meta.journal = item.get("container-title", [""])[0] if isinstance(item.get("container-title"), list) else item.get("container-title")
                if not meta.year:
                    y = item.get("issued", {}).get("date-parts", [[None]])[0][0]
                    meta.year = str(y) if y else None
                if not meta.doi:
                    meta.doi = item.get("DOI")
                if not meta.abstract:
                    abs_text = item.get("abstract")
                    if abs_text:
                        meta.abstract = re.sub(r"<[^>]+>", "", abs_text).strip()
                        meta.source = "CrossRef"
    return meta


def to_zotero_creators(authors: List[str]) -> List[dict]:
    creators = []
    for author in authors[:8]:
        a = author.strip()
        if not a:
            continue
        if "," in a:
            parts = [p.strip() for p in a.split(",", 1)]
            last = parts[0]
            first = parts[1] if len(parts) > 1 else ""
        else:
            parts = a.split()
            if len(parts) >= 2:
                last = parts[-1]
                first = " ".join(parts[:-1])
            else:
                last = a
                first = ""
        creators.append({"creatorType": "author", "firstName": first, "lastName": last})
    return creators


def zotero_call(endpoint: str, payload: Optional[dict] = None, binary: Optional[bytes] = None, extra_headers: Optional[dict] = None, timeout: int = 12):
    """通用 Zotero Connector 调用：成功返回（status, response_text, error）。"""
    url = f"{ZOTERO_URL}{endpoint}"
    data = b""
    headers = {
        "X-Zotero-Version": "6.0",
        "X-Zotero-Connector-API-Version": ZOTERO_VERSION_HEADER,
    }
    if extra_headers:
        headers.update(extra_headers)

    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif binary is not None:
        data = binary
    if binary is None and payload is None:
        method_type = "GET"
    else:
        method_type = "POST"

    req = urllib.request.Request(url, data=data or None, method=method_type)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            return resp.status, text, None
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        return e.code, txt, txt
    except Exception as e:
        return 0, "", str(e)


def import_one_pdf(
    pdf_path: Path,
    tags: List[str],
    item_type: str,
    collection_key: Optional[str],
    dry_run: bool = False,
    no_note: bool = False,
) -> ImportRecord:
    meta = parse_pdfinfo(pdf_path)
    meta = enrich_metadata(meta)

    if not meta.year:
        meta.year = None

    missing = []
    if not meta.title:
        missing.append("title")
    if not meta.authors:
        missing.append("authors")
    if not meta.year:
        missing.append("year")
    if not meta.journal:
        missing.append("journal")
    if not meta.doi:
        missing.append("doi")

    safe_title = normalize_filename(meta.title or pdf_path.stem)
    note_dir = WIKI_DIR / (pdf_path.relative_to(RAW_DIR).parts[0] if len(pdf_path.relative_to(RAW_DIR).parts) > 1 else "unclassified")
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{safe_title}.md"

    note_written = "未执行"
    summary = {"research_purpose": "", "model_architecture": "", "datasets": "", "core_conclusion": "", "refs_points": ""}

    # Zotero 导入
    status = "未执行"
    zotero_msg = "未尝试：Zotero 服务不可用"

    if dry_run:
        status = "未执行（dry-run）"
        zotero_msg = "未执行"
    else:
        session_id = hashlib.md5((str(pdf_path) + str(datetime.datetime.now())).encode("utf-8")).hexdigest()[:16]
        item_id = hashlib.md5(str(datetime.datetime.now().timestamp()).encode("utf-8")).hexdigest()[:8]
        zotero_item = {
            "itemType": item_type,
            "title": meta.title,
            "abstractNote": meta.abstract or "",
            "date": meta.year,
            "publicationTitle": meta.journal,
            "DOI": meta.doi,
            "url": meta.identifier,
            "archive": "",
            "language": "zh",
            "notes": "",
            "accessDate": datetime.date.today().isoformat(),
            "creators": to_zotero_creators(meta.authors),
            "tags": [{"tag": t} for t in tags],
            "id": item_id,
        }
        if collection_key:
            zotero_item["collections"] = [collection_key]

        payload = {
            "items": [zotero_item],
            "sessionID": session_id,
        }

        code, text_resp, err = zotero_call("saveItems", payload=payload)
        if code in (200, 201):
            # 成功入库后再做全文读取与附属笔记
            text = extract_fulltext(pdf_path)
            if text:
                summary = split_sections(text)
                meta.fulltext = text
                meta.fulltext_source = "pdftotext" if shutil.which("pdftotext") else "strings"
            else:
                meta.fulltext = None
                meta.fulltext_source = None
            if not meta.abstract:
                meta.abstract = summary["research_purpose"]

            if no_note:
                note_written = "未生成（--no-note）"
            else:
                try:
                    note_written = write_note(note_path, pdf_path, meta, summary)
                except Exception as e:
                    note_written = f"笔记生成失败: {e}"

            # 附件上传
            with open(pdf_path, "rb") as f:
                b = f.read()
            metadata = {
                "id": item_id,
                "url": f"file://{pdf_path}",
                "contentType": "application/pdf",
                "parentItemID": item_id,
                "title": meta.title,
                "sessionID": session_id,
                "tags": tags,
            }
            code2, resp2, err2 = zotero_call(
                "saveAttachment",
                payload=None,
                binary=b,
                extra_headers={
                    "Content-Type": "application/pdf",
                    "X-Metadata": json.dumps(metadata, ensure_ascii=True),
                },
                timeout=8,
            )
            if code2 in (200, 201):
                status = "成功"
                zotero_msg = "Zotero saveItems + saveAttachment 成功"
            else:
                status = "部分成功"
                zotero_msg = f"条目已保存，附件失败({code2}): {err2 or resp2}"
        elif code == 0:
            status = "未执行"
            zotero_msg = f"连接 Zotero 失败: {err}"
        else:
            status = "失败"
            zotero_msg = f"saveItems 失败({code}): {err or text_resp}"

    if status == "成功" and missing:
        status = "成功(元数据缺项)"

    return ImportRecord(
        pdf_path=pdf_path,
        title=meta.title or pdf_path.stem,
        status=status,
        zotero=zotero_msg,
        note=note_written,
        missing=missing,
    )


def write_note(note_path: Path, pdf_path: Path, meta: PdfMeta, summary: Dict[str, str]) -> str:
    # 结构化摘要字段（缺失时保留待补充）
    rp = summary.get("research_purpose") or "待补充：未解析到稳定段落，建议人工确认"
    ma = summary.get("model_architecture") or "待补充：未解析到稳定模型结构描述"
    ds = summary.get("datasets") or "待补充：未解析到稳定数据集描述"
    cc = summary.get("core_conclusion") or "待补充：未解析到稳定结论句"
    rf = summary.get("refs_points") or "待补充：未提取到可用参考要点"

    missing_fields = []
    if not meta.title:
        missing_fields.append("title")
    if not meta.authors:
        missing_fields.append("authors")
    if not meta.year:
        missing_fields.append("year")
    if not meta.journal:
        missing_fields.append("journal")
    if not meta.doi:
        missing_fields.append("doi")

    tag_lines = "\n".join(f"  - {t}" for t in MANDATORY_TAGS)
    author_lines = "\n".join(f"  - {a}" for a in (meta.authors or [])) or "  - "
    source_pdf = str(pdf_path.relative_to(ROOT))

    frontmatter = f"""---
title: "{meta.title}"
date: {datetime.date.today().isoformat()}
authors:
{author_lines}
year: {meta.year or ''}
journal: "{meta.journal or ''}"
source_pdf: [[{source_pdf}]]
tags:
{tag_lines}
key_finding: "待补充"
---
"""

    content = f"""{frontmatter}
# {meta.title}

> 论文来源：{meta.source}
> 识别文件：{source_pdf}

## 一句话

{meta.abstract or "待补充"}

## 结构化摘要

### 研究目的

{rp}

### 模型架构

{ma}

### 实验数据集

{ds}

### 核心结论

{cc}

### 参考文献要点

{rf}

## 元数据补全状态

- DOI：{meta.doi or "缺失"}
- 年份：{meta.year or "缺失"}
- 期刊/出版源：{meta.journal or "缺失"}
- 全文提取方式：{meta.fulltext_source or "未提取"}
- 缺失字段：{', '.join(missing_fields) if missing_fields else '无'}
"""
    note_path.write_text(content, encoding="utf-8")
    return str(note_path)


def save_report(reports: List[ImportRecord], dry_run: bool = False) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORT_DIR / f"zotero_raw_import_report_{ts}.md"

    ok = [r for r in reports if r.status.startswith("成功")]
    miss = [r for r in reports if r.missing]

    lines = ["# raw/papers Zotero 导入与摘要生成报表", f"生成时间：{datetime.datetime.now().isoformat(timespec='seconds')}", "", "## 结果", "| 文件 | 状态 | Zotero | 笔记 |", "| --- | --- | --- | --- |"]
    for r in reports:
        zot = r.zotero.replace("|", "\\|")
        note = r.note.replace("|", "\\|")
        lines.append(f"| `{r.pdf_path.relative_to(ROOT)}` | {r.status} | {zot} | {note} |")

    lines.append("")
    lines.append("## 元数据缺失条目")
    if not miss:
        lines.append("- 无")
    else:
        for r in miss:
            if r.missing:
                lines.append(f"- `{r.pdf_path.relative_to(ROOT)}` -> {', '.join(r.missing)}")

    lines.append("")
    lines.append(f"- 总计：{len(reports)}")
    lines.append(f"- 成功：{len(ok)}")

    content = "\n".join(lines)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        fallback_dir = Path("/private/tmp/note_zotero_reports")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_path = fallback_dir / path.name
        fallback_path.write_text(content, encoding="utf-8")
        path = fallback_path
    return path


def collect_pdfs(root: Path, max_count: Optional[int], pattern: str = "*.pdf") -> List[Path]:
    pdfs = sorted(root.rglob(pattern))
    if max_count:
        return pdfs[:max_count]
    return pdfs


def resolve_collection_flag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    # 仅在参数为 key 时直接生效
    if re.fullmatch(r"[A-Za-z0-9]{8,}", value):
        return value
    # 名称兜底尝试：若可查到数据库则返回 key
    return identify_collection_key(value, Path("/Users/bilibili/Zotero/zotero.sqlite"))


def main() -> int:
    parser = argparse.ArgumentParser(description="raw/papers 批量导入 Zotero 并生成附属笔记")
    parser.add_argument("--max", type=int, default=None, help="最多处理的论文数量")
    parser.add_argument("--collection", default="xxx", help="集合名或集合 key（未匹配到名称时不阻塞，导入到当前选中集合）")
    parser.add_argument("--item-type", default="journalArticle", help="Zotero 条目类型，默认 journalArticle")
    parser.add_argument("--dry-run", action="store_true", help="只做元数据扫描与笔记生成，不执行 Zotero 导入")
    parser.add_argument("--no-note", action="store_true", help="不生成/更新附属笔记")
    args = parser.parse_args()

    if not RAW_DIR.exists():
        print(f"找不到目录：{RAW_DIR}")
        return 2

    pdfs = collect_pdfs(RAW_DIR, args.max)
    if not pdfs:
        print(f"未找到 PDF：{RAW_DIR}")
        return 1

    collection_key = None
    if args.collection and not args.dry_run:
        collection_key = resolve_collection_flag(args.collection)
        if collection_key:
            print(f"使用集合 key: {collection_key}")
        else:
            print(f"未找到集合“{args.collection}”；将按当前 Zotero 选中位置导入")

    records = []
    for p in pdfs:
        try:
            rec = import_one_pdf(
                p,
                MANDATORY_TAGS,
                args.item_type,
                collection_key,
                dry_run=args.dry_run,
                no_note=args.no_note,
            )
            records.append(rec)
            print(f"{rec.status} | {p.relative_to(ROOT)}")
        except Exception as e:
            records.append(ImportRecord(pdf_path=p, title=p.stem, status="失败", zotero=f"脚本异常: {e}", note="", missing=[]))
            print(f"失败 | {p.relative_to(ROOT)} | {e}")

    report = save_report(records)
    print("")
    try:
        report_ref = report.relative_to(ROOT)
    except ValueError:
        report_ref = report
    print(f"报表：{report_ref}")
    print(f"总计: {len(records)}  成功: {sum(1 for r in records if r.status.startswith('成功'))}  失败: {sum(1 for r in records if r.status.startswith('失败'))}")
    print(f"元数据残缺条目：{sum(1 for r in records if bool(r.missing))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
