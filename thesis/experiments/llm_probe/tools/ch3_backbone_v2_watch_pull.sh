#!/usr/bin/env bash
# 监视服务器上 ch3_backbone_protocolA_v2 的三个骨干进程，
# 每个骨干一写出 exit-<骨干>.txt 就立刻增量拉回本机，不等其余骨干。
# 凭据只从 GPU_SSH_B76 / GPU_PWD_B76 读入并导出为 GPU_SSH_ACTIVE / GPU_PWD_ACTIVE，不打印。
set -u
set -o pipefail

PROJ="/Users/bilibili/personal/note/thesis/experiments/llm_probe"
REMOTE_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
REL="runs/diagnostics/ch3-backbone-protocolA-v2"
LOCAL_DIR="${PROJ}/${REL}"
WATCH_LOG="${LOCAL_DIR}/_watch/watch.log"
BACKBONES="gru transformer cnn"
INTERVAL="${INTERVAL:-90}"
MAX_ITER="${MAX_ITER:-160}"

mkdir -p "${LOCAL_DIR}/_watch"

if [ -z "${GPU_SSH_B76:-}" ] || [ -z "${GPU_PWD_B76:-}" ]; then
  echo "缺少必需环境变量：GPU_SSH_B76 / GPU_PWD_B76" >&2
  exit 2
fi
export GPU_SSH_ACTIVE="${GPU_SSH_B76}"
export GPU_PWD_ACTIVE="${GPU_PWD_B76}"

note() { printf '[%s] %s\n' "$(date '+%F %T')" "$1" | tee -a "${WATCH_LOG}"; }

note "监视启动：骨干=${BACKBONES} 间隔=${INTERVAL}s 上限=${MAX_ITER} 轮"

pulled=""
iter=0
while [ "${iter}" -lt "${MAX_ITER}" ]; do
  iter=$((iter + 1))

  done_list=$(expect "${PROJ}/tools/remote_exec/gpu_env_quiet.exp" \
    "cd ${REMOTE_ROOT} && echo __CODEX_RESULT_BEGIN__; ls ${REL}/exit-*.txt 2>/dev/null; echo __CODEX_RESULT_END__" 2>>"${WATCH_LOG}")
  rc=$?
  if [ "${rc}" -ne 0 ]; then
    note "远程查询失败，退出码=${rc}，本轮跳过"
    sleep "${INTERVAL}"
    continue
  fi

  for b in ${BACKBONES}; do
    case " ${pulled} " in *" ${b} "*) continue ;; esac
    case "${done_list}" in
      *"exit-${b}.txt"*)
        note "骨干 ${b} 已结束，开始拉回"
        expect "${PROJ}/tools/remote_exec/gpu_rsync_pull.exp" \
          "${REMOTE_ROOT}/${REL}/${b}" "${LOCAL_DIR}/" >>"${WATCH_LOG}" 2>&1
        rc1=$?
        expect "${PROJ}/tools/remote_exec/gpu_rsync_pull.exp" \
          "${REMOTE_ROOT}/${REL}/launch-${b}.log" "${LOCAL_DIR}/" >>"${WATCH_LOG}" 2>&1
        rc2=$?
        expect "${PROJ}/tools/remote_exec/gpu_rsync_pull.exp" \
          "${REMOTE_ROOT}/${REL}/exit-${b}.txt" "${LOCAL_DIR}/" >>"${WATCH_LOG}" 2>&1
        rc3=$?
        if [ "${rc1}" -eq 0 ] && [ "${rc2}" -eq 0 ] && [ "${rc3}" -eq 0 ]; then
          note "骨干 ${b} 拉回完成，退出码=$(cat "${LOCAL_DIR}/exit-${b}.txt" 2>/dev/null | tr -d '\n')"
          pulled="${pulled} ${b}"
        else
          note "骨干 ${b} 拉回失败：rc=${rc1}/${rc2}/${rc3}，下轮重试"
        fi
        ;;
    esac
  done

  n=0
  for b in ${pulled}; do n=$((n + 1)); done
  if [ "${n}" -eq 3 ]; then
    note "三个骨干全部拉回完成，监视结束"
    exit 0
  fi

  sleep "${INTERVAL}"
done

note "达到轮次上限仍未全部完成，已拉回：${pulled}"
exit 1
