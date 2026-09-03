#!/usr/bin/env bash
#
# tools/pdf_to_fulltext.sh —— 把 raw/ 下的 PDF 原件批量转换为可检索的全文 Markdown。
#
# ============================================================================
# 为什么只用 `mineru-open-api extract`，本脚本不提供 flash-extract 选项
# ============================================================================
#
# flash-extract 有两个致命限制，都会在本仓库的实际语料上触发：
#   1. 上限 10 MB / 20 页。本仓库最大的 PDF 达 36 MB
#      （raw/papers/pinn/2410.13228.pdf），多篇论文超过 20 页，
#      flash-extract 会直接报错或强制截断，而不是产出完整全文。
#   2. 公式与表格会被替换成占位符，公式符号直接丢失。本仓库已经因为用
#      flash-extract 的输出推导过错误公式（见
#      `.Codex/docs/RWKV/RWKV第三章恢复卡.md` 「A2」节的事故记录）。
#
# 本仓库已经配置了 MinerU 精确模式的 token（`mineru-open-api auth --show`
# 可核验），extract 支持 200 MB / 600 页，默认开启公式与表格识别。
# 2026-09-03 同一会话内主代理已经三次错用 flash-extract——教训是
# "记得用 extract" 这件事必须焊进脚本本身，不能指望人或代理每次都记得，
# 所以本脚本从源头上不接受任何 flash 相关参数。
#
# ============================================================================
# 落点规则
# ============================================================================
#
#   raw/papers/<子路径>/<原名>.pdf  →  wiki/papers/<子路径>/<原名>-全文.md
#   raw/<原名>.pdf（不在 papers/ 下）→  wiki/papers/<原名>-全文.md
#
# 产出的 Markdown 带最小 YAML 前言（title / date / tags / source_pdf），
# 满足 scripts/literature_search 对 wiki/papers/**/*.md 的索引前提
# （合法 YAML 前言 + 非空 source_pdf，见该工具 documents.py::scan_notes）。
# 这是 MinerU 的机械全文转换产物，不是 SCHEMA.md「类型/论文」要求的
# 结构化理解笔记（背景/方法核心/我的理解等）——两者是不同的知识层对象，
# 正文中会显式声明这一点，避免被误当作已精读的笔记。
#
# 原件中的图片（MinerU 转换的中间产物）按 wiki/AGENTS.md「不在知识层保存
# PDF 转换中间文件」的规定不落库，只写入系统临时目录后丢弃；因此正文中的
# 图片引用链接可能失效，这是预期行为，不是缺陷。
#
# ============================================================================
# 用法
# ============================================================================
#
#   tools/pdf_to_fulltext.sh                        # 转换 raw/ 下全部 PDF
#   tools/pdf_to_fulltext.sh raw/papers/rwkv         # 只转换某个目录（递归）
#   tools/pdf_to_fulltext.sh raw/papers/x/foo.pdf    # 只转换单个文件
#   tools/pdf_to_fulltext.sh --jobs 2 raw/papers/x   # 降低并发（默认且上限为 4）
#   tools/pdf_to_fulltext.sh --force raw/papers/x    # 忽略已有产出，强制重转
#   tools/pdf_to_fulltext.sh --failures /path/to.md  # 自定义失败清单落点
#
# 幂等：目标 .md 已存在且非空则跳过，不重复调用 API。
# 并发：默认 4，硬上限 4（避免触发 MinerU API 限流），传更大的值会被自动降到 4。
# 失败：调用失败或产出为空时重试 1 次；仍失败则原样保留旧产出（如有），
#       并把文件名与错误信息追加写入失败清单文件，不静默跳过。
#
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_FAILLOG="$REPO_ROOT/.Codex/docs/pdf-to-fulltext-failures.md"

usage() {
  cat <<'EOF'
用法: tools/pdf_to_fulltext.sh [选项] [PATH ...]

  PATH               PDF 文件或目录（可重复给出）；不给出时默认转换 raw/ 全部 PDF。
  --jobs N           并发进程数，默认 4，硬上限 4（超过会被自动降到 4）。
  --force            忽略已有产出，强制重新转换。
  --failures PATH    失败清单文件路径，默认 .Codex/docs/pdf-to-fulltext-failures.md（追加写入）。
  -h, --help         显示本帮助。

只使用 mineru-open-api extract（精确模式），不提供 flash-extract 选项。
EOF
}

# ============================================================================
# --worker 模式：由主流程通过 xargs -P 并发调用自身，一次只处理一个 PDF。
# ============================================================================
if [[ "${1:-}" == "--worker" ]]; then
  shift
  SRC_ABS="$1"
  FORCE="${PDF2MD_FORCE:-0}"
  FAILLOG="${PDF2MD_FAILLOG:-$DEFAULT_FAILLOG}"
  TODAY="${PDF2MD_TODAY:-$(date +%F)}"

  # 注意：下面两处 FAIL 故意写到 stdout（不是 stderr），原因见文末统计逻辑的说明。
  REL="${SRC_ABS#"$REPO_ROOT"/}"
  if [[ "$REL" == "$SRC_ABS" ]]; then
    echo "FAIL  $SRC_ABS: 不在仓库 $REPO_ROOT 下，跳过"
    printf -- '- [%s] `%s`：不在仓库 %s 下\n' "$(date '+%F %T')" "$SRC_ABS" "$REPO_ROOT" >> "$FAILLOG"
    exit 0
  fi
  case "$REL" in
    raw/papers/*) SUB="${REL#raw/papers/}" ;;
    raw/*) SUB="${REL#raw/}" ;;
    *)
      echo "FAIL  $REL: 不在 raw/ 下，本工具只处理 raw/ 原件"
      printf -- '- [%s] `%s`：不在 raw/ 下，本工具只处理 raw/ 原件\n' "$(date '+%F %T')" "$REL" >> "$FAILLOG"
      exit 0
      ;;
  esac

  STEM="${SUB%.[Pp][Dd][Ff]}"
  TARGET_REL="wiki/papers/${STEM}-全文.md"
  TARGET_ABS="$REPO_ROOT/$TARGET_REL"

  if [[ "$FORCE" != "1" && -s "$TARGET_ABS" ]]; then
    echo "SKIP  $REL（目标已存在且非空：$TARGET_REL）"
    exit 0
  fi

  BASE_NAME="$(basename "$REL")"
  TITLE="${BASE_NAME%.[Pp][Dd][Ff]}"
  TITLE_ESC="${TITLE//\\/\\\\}"
  TITLE_ESC="${TITLE_ESC//\"/\\\"}"
  case "$SUB" in
    */*) DOMAIN_TAG="${SUB%%/*}" ;;
    *) DOMAIN_TAG="根目录" ;;
  esac

  OK=0
  ERR=""
  for attempt in 1 2; do
    TMP_OUT="$(mktemp -d "${TMPDIR:-/tmp}/pdf2md.XXXXXX")"
    if OUT="$(mineru-open-api extract "$SRC_ABS" -o "$TMP_OUT/" --timeout 300 2>&1)"; then
      PRODUCED="$(find "$TMP_OUT" -maxdepth 1 -type f -iname '*.md' -print -quit)"
      if [[ -n "$PRODUCED" && -s "$PRODUCED" ]]; then
        mkdir -p "$(dirname "$TARGET_ABS")"
        TMP_FINAL="$(mktemp "${TMPDIR:-/tmp}/pdf2md-final.XXXXXX")"
        {
          echo '---'
          printf 'title: "%s"\n' "$TITLE_ESC"
          echo "date: $TODAY"
          echo 'tags:'
          echo '  - 类型/全文转换'
          printf '  - "%s"\n' "$DOMAIN_TAG"
          printf 'source_pdf: "%s"\n' "$REL"
          echo '---'
          echo
          echo '> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。'
          echo
          cat "$PRODUCED"
        } > "$TMP_FINAL"
        mv "$TMP_FINAL" "$TARGET_ABS"
        rm -rf "$TMP_OUT"
        OK=1
        break
      else
        ERR="extract 退出成功但未产出非空 markdown（可能是扫描件需要 --ocr，或格式不受支持）"
      fi
    else
      ERR="$(printf '%s' "$OUT" | tail -5 | tr '\n' ' ')"
    fi
    rm -rf "$TMP_OUT"
  done

  if [[ "$OK" == "1" ]]; then
    echo "OK    $REL -> $TARGET_REL"
  else
    # 注意：故意写到 stdout（不是 stderr），因为主流程靠扫描 stdout 里的
    # OK/SKIP/FAIL 前缀行来统计成功/跳过/失败数量；写到 stderr 会导致统计遗漏。
    echo "FAIL  $REL: $ERR"
    printf -- '- [%s] `%s`：%s\n' "$(date '+%F %T')" "$REL" "$ERR" >> "$FAILLOG"
  fi
  exit 0
fi

# ============================================================================
# 主流程：解析参数、收集 PDF 列表、幂等交给 worker、并发派发
# ============================================================================

if ! command -v mineru-open-api >/dev/null 2>&1; then
  echo "错误：未找到 mineru-open-api，请先安装（见 pdf-converter 技能说明）" >&2
  exit 1
fi

JOBS=4
FORCE=0
FAILLOG="$DEFAULT_FAILLOG"
INPUT_PATHS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobs)
      JOBS="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --failures)
      FAILLOG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "错误：未知选项 $1" >&2
      usage
      exit 1
      ;;
    *)
      INPUT_PATHS+=("$1")
      shift
      ;;
  esac
done

if ! [[ "$JOBS" =~ ^[0-9]+$ ]] || [[ "$JOBS" -lt 1 ]]; then
  echo "错误：--jobs 必须是正整数" >&2
  exit 1
fi
if [[ "$JOBS" -gt 4 ]]; then
  echo "警告：并发度上限为 4（避免触发 MinerU API 限流），已从 $JOBS 降至 4" >&2
  JOBS=4
fi

if [[ ${#INPUT_PATHS[@]} -eq 0 ]]; then
  INPUT_PATHS=("raw")
fi

PDFS=()
for p in "${INPUT_PATHS[@]}"; do
  if [[ -d "$p" ]]; then
    ABS_DIR="$(cd "$p" && pwd)"
  elif [[ -d "$REPO_ROOT/$p" ]]; then
    ABS_DIR="$(cd "$REPO_ROOT/$p" && pwd)"
  else
    ABS_DIR=""
  fi
  if [[ -n "$ABS_DIR" ]]; then
    while IFS= read -r -d '' f; do
      PDFS+=("$f")
    done < <(find "$ABS_DIR" -type f -iname '*.pdf' -print0)
    continue
  fi
  if [[ -f "$p" ]]; then
    PDFS+=("$(cd "$(dirname "$p")" && pwd)/$(basename "$p")")
    continue
  fi
  if [[ -f "$REPO_ROOT/$p" ]]; then
    PDFS+=("$(cd "$(dirname "$REPO_ROOT/$p")" && pwd)/$(basename "$p")")
    continue
  fi
  echo "警告：路径不存在，跳过：$p" >&2
done

if [[ ${#PDFS[@]} -eq 0 ]]; then
  echo "没有找到待处理的 PDF"
  exit 0
fi

mkdir -p "$(dirname "$FAILLOG")"
touch "$FAILLOG"

export PDF2MD_FORCE="$FORCE"
export PDF2MD_FAILLOG="$FAILLOG"
export PDF2MD_TODAY="$(date +%F)"

RESULTS_FILE="$(mktemp "${TMPDIR:-/tmp}/pdf2md-results.XXXXXX")"
trap 'rm -f "$RESULTS_FILE"' EXIT

printf '%s\0' "${PDFS[@]}" | xargs -0 -n1 -P "$JOBS" "$SCRIPT_PATH" --worker | tee "$RESULTS_FILE"

OK_N=$(grep -c '^OK' "$RESULTS_FILE" || true)
SKIP_N=$(grep -c '^SKIP' "$RESULTS_FILE" || true)
FAIL_N=$(grep -c '^FAIL' "$RESULTS_FILE" || true)

echo ""
echo "完成：共 ${#PDFS[@]} 篇，成功 $OK_N，跳过 $SKIP_N，失败 $FAIL_N"
if [[ "$FAIL_N" -gt 0 ]]; then
  echo "失败清单见：$FAILLOG"
fi
