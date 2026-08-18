#!/usr/bin/env bash
# 断点续训审计（四格整跑，含阶段闸门与 LSPR24 评价）
#   A 连续整跑；B 在第三格训练中途 SIGKILL 后重启；C 在评价阶段第一格评完后 SIGKILL 后重启
set -u
BK=$1; NE=$2; ES=$3; ROOT=$4
cd /root/autodl-tmp/thesis/experiments/llm_probe || exit 90
source tools/env/activate.sh >/dev/null 2>&1 || true
BASE="$ROOT/full4-${BK}"
rm -rf "$BASE"; mkdir -p "$BASE/A" "$BASE/B" "$BASE/C"
CMD=(uv run --no-sync python tools/ch3_backbone_protocolA_v2.py --backbone "$BK"
     --n-epoch "$NE" --epoch-steps "$ES" --skip-impl-verify)

echo "=== [full4 $BK] A 连续整跑 ==="
"${CMD[@]}" --out-root "$BASE/A" > "$BASE/A/run.log" 2>&1; echo "  exit=$?"

kill_after () {   # $1=outdir $2=logname $3=触发子串
  setsid "${CMD[@]}" --out-root "$1" > "$1/$2" 2>&1 &
  local PID=$! PGID K=0
  PGID=$(ps -o pgid= -p "$PID" | tr -d ' ')
  for _ in $(seq 1 9000); do
    if grep -qF "$3" "$1/$2" 2>/dev/null; then sleep 1; kill -9 -"$PGID" 2>/dev/null; K=1; break; fi
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.4
  done
  wait "$PID" 2>/dev/null
  echo "  KILLED=$K  触发串=[$3]"
}

echo "=== [full4 $BK] B 第三格训练中途杀 ==="
kill_after "$BASE/B" run1.log "${BK}-C10 ep  1/${NE}"
echo "  --- 杀后 progress.jsonl ---"; cat "$BASE/B/$BK/progress.jsonl" 2>&1
echo "  --- 残留临时文件 ---"; find "$BASE/B" \( -name '*.tmp' -o -name '*.partial' \) -print 2>&1
"${CMD[@]}" --out-root "$BASE/B" > "$BASE/B/run2.log" 2>&1; echo "  exit2=$?"
grep -E "恢复|跳过|闸门|隔离断言|读入 LSPR24" "$BASE/B/run2.log" 2>&1

echo "=== [full4 $BK] C 评价阶段中途杀 ==="
kill_after "$BASE/C" run1.log "${BK}-C01: epoch="
echo "  --- 杀后 eval_progress.jsonl ---"; cat "$BASE/C/$BK/eval_progress.jsonl" 2>&1
echo "  --- 残留临时文件 ---"; find "$BASE/C" \( -name '*.tmp' -o -name '*.partial' \) -print 2>&1
"${CMD[@]}" --out-root "$BASE/C" > "$BASE/C/run2.log" 2>&1; echo "  exit2=$?"
grep -E "恢复|跳过|闸门|隔离断言|读入 LSPR24" "$BASE/C/run2.log" 2>&1

echo "=== [full4 $BK] 比较 ==="
for V in B C; do
  for c in C00 C01 C10 C11; do
    echo "##### selected.pt  A vs $V  格 $c #####"
    uv run --no-sync python tools/_resume_audit/cmp_ckpt.py \
      "$BASE/A/$BK/cells/${BK}-${c}/selected.pt" "$BASE/$V/$BK/cells/${BK}-${c}/selected.pt" 2>&1 \
      | grep -E "max_abs_diff|not_bitwise_equal\"|bitwise_equal|val_ap_|epoch_" | grep -v file_
  done
  echo "##### 结果 JSON  A vs $V （cells 指标逐位）#####"
  uv run --no-sync python - "$BASE/A/$BK/ch3_backbone_protocolA_results.json" \
      "$BASE/$V/$BK/ch3_backbone_protocolA_results.json" <<'PYX'
import json, sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
bad=[]
for k in a["cells"]:
    for m in ["sel_epoch","val_ap","p","fap","fauc","e_max","e_lp","dr_main","dr_max","n_ent_scored","npar"]:
        if repr(a["cells"][k][m])!=repr(b["cells"][k][m]):
            bad.append([k,m,repr(a["cells"][k][m]),repr(b["cells"][k][m])])
print("cells 指标逐位不同项:", json.dumps(bad, ensure_ascii=False))
print("交互项逐位相同:", repr(a["interaction"])==repr(b["interaction"]))
print("A isolation:", a["isolation"], " / ", sys.argv[2].split('/')[-3], b["isolation"])
print("resume:", b["resume"]["cells_trained_this_process"], b["resume"]["cells_resumed_from_disk"],
      b["resume"]["cells_evaluated_this_process"], b["resume"]["cells_eval_resumed_from_disk"])
PYX
  for c in C11; do
    echo "##### scores_${BK}_C11.npy  A vs $V #####"
    uv run --no-sync python - "$BASE/A/$BK/scores_${BK}_C11.npy" "$BASE/$V/$BK/scores_${BK}_C11.npy" <<'PYY'
import numpy as np, sys
a=np.load(sys.argv[1]); b=np.load(sys.argv[2])
print("shape", a.shape, b.shape, "逐位相同:", bool(np.array_equal(a,b)), "最大绝对差:", float(np.abs(a-b).max()))
PYY
  done
done
