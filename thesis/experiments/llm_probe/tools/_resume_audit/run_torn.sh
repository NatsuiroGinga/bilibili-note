#!/usr/bin/env bash
# 断裂追加台账（torn append）鲁棒性探针：
# append_jsonl 不是原子的。若断电时最后一行只写了一半且没有换行，
# 下一次运行追加的新记录会被粘到半行后面，两条一起变成不可解析行。
# 本探针复现该状态，检验脚本能否自愈。
set -u
ROOT=$1
cd /root/autodl-tmp/thesis/experiments/llm_probe || exit 90
source tools/env/activate.sh >/dev/null 2>&1 || true
SRC="$ROOT/full4-cnn/A"
DST="$ROOT/torn-cnn"
rm -rf "$DST"; mkdir -p "$DST"
cp -r "$SRC/cnn" "$DST/cnn"
P="$DST/cnn/progress.jsonl"
echo "--- 原始 progress.jsonl 行数 ---"; wc -l < "$P"
# 去掉最后一行（C11），换成同一条记录的前 60 个字符且不带换行，模拟断裂写
head -n 3 "$P" > "$P.new"
tail -n 1 "$P" | cut -c1-60 | tr -d '\n' >> "$P.new"
mv "$P.new" "$P"
echo "--- 制造断裂写之后 ---"; cat "$P" | tail -c 200; echo; echo "(末行无换行)"
echo "=== 原命令重启 ==="
uv run --no-sync python tools/ch3_backbone_protocolA_v2.py --backbone cnn \
  --n-epoch 3 --epoch-steps 400 --skip-impl-verify --out-root "$DST" > "$DST/rerun.log" 2>&1
echo "  exit=$?"
tail -25 "$DST/rerun.log"
echo "--- 重启后 progress.jsonl 末尾 ---"; tail -c 400 "$P"; echo
echo "=== 再重启一次（检验是否可自愈） ==="
uv run --no-sync python tools/ch3_backbone_protocolA_v2.py --backbone cnn \
  --n-epoch 3 --epoch-steps 400 --skip-impl-verify --out-root "$DST" > "$DST/rerun2.log" 2>&1
echo "  exit=$?"
tail -12 "$DST/rerun2.log"
