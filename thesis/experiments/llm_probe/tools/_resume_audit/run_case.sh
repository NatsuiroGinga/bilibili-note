#!/usr/bin/env bash
# 断点续训审计（单格）：A 连续跑一 / A2 连续跑二 / B 中断恢复跑
set -u
BK=$1; CELL=$2; NE=$3; ES=$4; ROOT=$5
cd /root/autodl-tmp/thesis/experiments/llm_probe || exit 90
source tools/env/activate.sh >/dev/null 2>&1 || true
BASE="$ROOT/${BK}-${CELL}"
rm -rf "$BASE"; mkdir -p "$BASE/A" "$BASE/A2" "$BASE/B"

run_full () {
  uv run --no-sync python tools/ch3_backbone_protocolA_v2.py \
    --backbone "$BK" --cells "$CELL" --n-epoch "$NE" --epoch-steps "$ES" \
    --skip-impl-verify --out-root "$1" > "$1/run.log" 2>&1
  echo "  exit=$?"
}

echo "=== [$BK-$CELL] A 连续跑一 ==="; run_full "$BASE/A"
echo "=== [$BK-$CELL] A2 连续跑二 ==="; run_full "$BASE/A2"
echo "=== [$BK-$CELL] B 中断跑（第一次启动） ==="
setsid uv run --no-sync python tools/ch3_backbone_protocolA_v2.py \
  --backbone "$BK" --cells "$CELL" --n-epoch "$NE" --epoch-steps "$ES" \
  --skip-impl-verify --out-root "$BASE/B" > "$BASE/B/run1.log" 2>&1 &
PID=$!; PGID=$(ps -o pgid= -p "$PID" | tr -d ' '); KILLED=0; PREV=$((NE-1))
for _ in $(seq 1 6000); do
  if grep -q "ep  ${PREV}/${NE}" "$BASE/B/run1.log" 2>/dev/null; then
    sleep 2; kill -9 -"$PGID" 2>/dev/null; KILLED=1; break
  fi
  kill -0 "$PID" 2>/dev/null || break
  sleep 0.5
done
wait "$PID" 2>/dev/null
echo "  KILLED=$KILLED"
echo "  --- 残留临时文件 ---"; find "$BASE/B" \( -name '*.tmp' -o -name '*.partial' \) -print 2>&1
echo "=== [$BK-$CELL] B 原命令重启 ==="
uv run --no-sync python tools/ch3_backbone_protocolA_v2.py \
  --backbone "$BK" --cells "$CELL" --n-epoch "$NE" --epoch-steps "$ES" \
  --skip-impl-verify --out-root "$BASE/B" > "$BASE/B/run2.log" 2>&1
echo "  exit2=$?"; grep -E "恢复|ep +[0-9]+/" "$BASE/B/run2.log" 2>&1
echo "=== [$BK-$CELL] 比较 ==="
for pair in "A A2" "A B"; do
  set -- $pair
  for f in selected inflight; do
    echo "##### $f  $1 vs $2 #####"
    uv run --no-sync python tools/_resume_audit/cmp_ckpt.py \
      "$BASE/$1/$BK/cells/${BK}-${CELL}/$f.pt" "$BASE/$2/$BK/cells/${BK}-${CELL}/$f.pt" 2>&1 \
      | grep -E "max_abs_diff|not_bitwise_equal\"|bitwise_equal|_a\"|_b\"" | grep -v file_
  done
done
