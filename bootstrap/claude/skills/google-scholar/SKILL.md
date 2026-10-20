---
name: google-scholar
description: This skill should be used when the user asks to "search Google Scholar", "find academic papers", "scholar search", "lookup papers", "find citations", "academic search", "search for papers by author", "find journal articles", "get BibTeX", "cite this paper", "download paper", or needs to search Google Scholar for academic literature via the scholar CLI tool.
version: 0.2.0
user-invocable: false
---

# Google Scholar CLI (scholar)

Search Google Scholar for academic papers via the `scholar` command-line tool.

**Requires:** `scholar` on PATH (`~/.local/bin/scholar` → `~/projects/google-scholar-cli/scholar`)

**Check:** `command -v scholar || echo "MISSING: scholar CLI not installed"`

## ⚠️ 本机必须挂代理（2026-10-15 实测）

本机**直连** `scholar.google.com` 返回 `HTTP 000`（不通）；**必须走本机代理端口 7890**：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
  scholar lookup "<查询>" --json
```

实测对照（同一条查询）：

| 方式 | 结果 |
| --- | --- |
| 直连 | `HTTP 000`（失败） |
| 走 `127.0.0.1:7890` | `HTTP 200`，正常返回 JSON |

**不挂代理时报 `Unable to connect`。** 此前有一次会话因未挂代理而失败，随后退回 WebSearch——**该次 WebSearch 给出的 arXiv ID 幻觉率 4/4**（用 arXiv 主站按标题重检后全部指向无关论文）。

**⇒ 失败时挂代理重试，不得改用 WebSearch 替代 `scholar`。** 在线检索结果一律只作候选；核原文须用 arXiv 或出版社主站按标题重新定位 ID。

## IRON LAW: No Hallucinated Metadata

**NEVER fabricate paper titles, authors, journals, years, or abstracts from memory.**

When the user asks about a specific paper or needs citation details:

```
User mentions a paper
    ↓
Do you have the exact metadata from a scholar command in this session?
    ↓
YES → Use that data
NO  → Run scholar search/lookup --bibtex FIRST, then report
```

### Metadata Facts

- Training-data paper metadata is unreliable even for famous papers — wrong years, missing co-authors, garbled titles. Presenting remembered metadata is an unverified claim presented as fact; run `scholar lookup "title" --bibtex` first, then report.
- `--bibtex` adds seconds, not minutes, and the BibTeX includes the abstract — reconstructing either from memory is counterproductive on its own terms.

### Red Flags

- **About to type a paper title from memory** → STOP. Run `scholar lookup`.
- **About to list authors without a source** → STOP. Run `--bibtex`.
- **Saying "published in" without verification** → STOP. Check the BibTeX.
- **Writing an abstract from memory** → STOP. BibTeX includes the abstract.

## Authentication

Before first use, authenticate by extracting cookies from an active Chrome session:

```bash
# Chrome must be running with remote debugging enabled
scholar auth --port 9222
```

Cookies are stored in `~/.google-scholar/cookies` (mode 0600).

## Core Commands

### Scholar Labs Search (AI-Enhanced)

Natural language search using Google Scholar Labs API:

```bash
# One-shot search
scholar search "what are the key papers on attention mechanisms"

# JSON output for parsing
scholar search "corporate disclosure and information asymmetry" --json

# With BibTeX citations (includes abstracts)
scholar search "attention is all you need" --bibtex

# Download PDFs for results with full-text links
scholar search "transformer architectures" --download

# Interactive multi-turn mode (follow-up questions)
scholar search --interactive
```

### Traditional Keyword Search

Standard Google Scholar full-text search:

```bash
# Keyword search
scholar lookup "machine learning transformers"

# Author search
scholar lookup "author:shleifer disclosure" --json

# With BibTeX
scholar lookup "asset pricing" --bibtex

# With PDF download
scholar lookup "deep learning" --download
```

### Cite (BibTeX by Cluster ID)

Fetch BibTeX directly when you already have a cluster ID from search results:

```bash
# Single paper
scholar cite 5Gohgn6QFikJ

# Multiple papers, JSON output
scholar cite 5Gohgn6QFikJ 8409835334886051453 --json
```

### Download (Single PDF)

**Note:** `--download` works for open-access PDFs (arXiv, NBER, etc.) but is unreliable for papers behind library link resolvers (institutional access). For paywalled papers, return the URL and let the user download manually.

```bash
scholar download "https://arxiv.org/pdf/1706.03762" --output attention.pdf
```

## Quick Reference

| Need | Command |
|------|---------|
| Natural language question | `scholar search "question"` |
| Keyword/author search | `scholar lookup "keywords"` |
| BibTeX citations | Add `--bibtex` to search/lookup |
| BibTeX by cluster ID | `scholar cite <clusterId>` |
| Download PDFs | Add `--download` to search/lookup |
| Download single PDF | `scholar download "url" --output file.pdf` |
| JSON output | Add `--json` to any command |
| Interactive follow-ups | `scholar search --interactive` |
| Re-authenticate | `scholar auth` |

## Decision Tree: Which Command?

```
Do you have a cluster ID already?
  YES → scholar cite <clusterId>
  NO  ↓
Do you have a natural language research question?
  YES → scholar search "question"
  NO  ↓
Do you need keyword-exact or author-specific results?
  YES → scholar lookup "author:name keyword"
  NO  ↓
Do you want follow-up refinement?
  YES → scholar search --interactive
```

**When to add flags:**

```
Need citation metadata (authors, journal, year, abstract)?
  YES → Add --bibtex
Need to download the PDF (open-access only)?
  YES → Add --download (unreliable for paywalled papers — return the URL instead)
Need machine-readable output?
  YES → Add --json
```

## Verified Paper Information Workflow

When presenting paper information to the user, follow this workflow:

```
1. Run scholar search/lookup with --bibtex
2. Parse BibTeX fields for authoritative metadata:
   - title, author, journal/booktitle, year, abstract
3. Present ONLY the fields returned by BibTeX
4. If BibTeX is missing a field, say "not available" — do NOT fill from memory
```

**BibTeX includes abstracts:** The `--bibtex` flag injects the snippet as an `abstract` field in the BibTeX entry. Use this instead of generating abstracts.

## Output Format

**Table output (default):** Columns for #, Title, Authors, Year, Cited, Journal, followed by snippets and URLs.

**JSON output (`--json`):** Array of `ScholarResult` objects:

```json
{
  "title": "Paper Title",
  "authors": "Author A, Author B",
  "journal": "Journal Name",
  "year": "2024",
  "citations": 150,
  "snippet": "Abstract excerpt...",
  "url": "https://...",
  "pdfUrl": "https://... or null",
  "clusterId": "12345",
  "position": 1
}
```

**BibTeX output (`--bibtex`):** Standard BibTeX entries with abstract field:

```bibtex
@article{key,
  title={Paper Title},
  author={Author, A and Author, B},
  journal={Journal Name},
  year={2024},
  abstract={Abstract text from Google Scholar snippet...}
}
```

## Domain Knowledge Integration

When searching Google Scholar, ALWAYS consult the domain knowledge file first:

**File:** `domain-knowledge.local.md` (relative to this skill's base directory)

This file contains the user's curated list of trusted journals, authors, and research groups. Use it to:

1. **Prioritize results** from known-good journals and authors
2. **Flag unfamiliar sources** - if a result is from an unknown journal, note it
3. **Suggest related searches** - use known authors to refine queries
4. **Assess quality** - weight results higher when they appear in trusted venues

### How to Use Domain Knowledge

```
User asks: "find papers on corporate disclosure"
    ↓
1. Read domain-knowledge.local.md
2. Run scholar search/lookup
3. Cross-reference results against trusted journals/authors
4. Present results with quality signals:
   - ★ = from trusted journal or by trusted author
   - Results from unknown sources shown without star
```

## Operational Rules

1. **No hallucinated metadata** — NEVER cite title/author/journal/year/abstract from memory. Use `--bibtex` or `scholar cite` to get verified data.
2. **Scholar is for discovery** — Use it to find new papers, not to read them
3. **Always use `--json`** when results will be processed programmatically
4. **Use `--bibtex` when presenting papers** — It provides verified author, journal, year, and abstract fields
5. **Cross-reference domain knowledge** — Always check trusted journals/authors
6. **Auth required** — If search fails with auth errors, re-run `scholar auth`
7. **Rate limits** — Google Scholar may rate-limit; space out rapid queries
