#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
manifest="$project_root/runs/data-prepared/lspr24-screen-wide-v1/dataset-manifest.json"
output_dir="$project_root/runs/baselines/lspr24-screen-tabular-seed42-v2"
launcher_dir="$project_root/runs/launchers/lspr24-screen-tabular-seed42-v2"
run_name="lspr24-screen-tabular-seed42-v2"

cd "$project_root"
source tools/env/activate.sh

if [[ ! -s "$manifest" ]]; then
  printf '%s\n' "阻断：数据清单不存在或为空：$manifest" >&2
  exit 66
elif [[ ! -f scripts/run_lspr24_screen_baselines.sh ]]; then
  printf '%s\n' '阻断：统一基线启动脚本不存在。' >&2
  exit 67
elif [[ ! -f src/flow_probe/lspr24_screen_dataset.py || ! -f src/flow_probe/lspr24_screen_baselines.py ]]; then
  printf '%s\n' '阻断：统一基线数据加载器或模型入口不存在。' >&2
  exit 68
elif [[ -e "$launcher_dir" || -e "$output_dir" ]]; then
  printf '%s\n' '阻断：本次唯一运行目录已存在，拒绝覆盖或重复启动。' >&2
  exit 73
fi

backup_manifest="${manifest%.json}.relative-path-backup.json"
if [[ -e "$backup_manifest" ]]; then
  if ! cmp -s "$manifest" "$backup_manifest"; then
    printf '%s\n' '阻断：相对路径清单备份已存在且原清单已变化。' >&2
    exit 74
  fi
else
  cp -p "$manifest" "$backup_manifest"
fi
python -c 'import json, os, sys; from pathlib import Path; manifest = Path(sys.argv[1]); root = Path(sys.argv[2]).resolve(); document = json.loads(manifest.read_text(encoding="utf-8")); artifacts = document["artifacts"]; resolve_artifact = lambda raw: (Path(raw) if Path(raw).is_absolute() else root / raw).resolve(); paths = {name: resolve_artifact(str(entry["path"])) for name, entry in artifacts.items()}; invalid = any(("final" in path.relative_to(root).parts) or not path.is_file() for path in paths.values()); invalid and (_ for _ in ()).throw(ValueError("制品路径越界、指向最终切分或不存在")); [artifacts[name].__setitem__("path", str(path)) for name, path in paths.items()]; temporary = manifest.with_suffix(".json.partial"); temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, manifest)' "$manifest" "$project_root"

mkdir -p "$launcher_dir"
printf '%s\n' 'running' >"$launcher_dir/status.txt"
date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/started_at.txt"

set +e
bash scripts/run_lspr24_screen_baselines.sh \
  "$manifest" \
  "$output_dir" \
  "$run_name" 2>&1 | tee "$launcher_dir/launcher.log"
pipeline_status=("${PIPESTATUS[@]}")
set -e

model_code="${pipeline_status[0]}"
tee_code="${pipeline_status[1]}"
printf '%s\n' "$model_code" >"$launcher_dir/model-exit-code.txt"
printf '%s\n' "$tee_code" >"$launcher_dir/tee-exit-code.txt"
date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/finished_at.txt"

if [[ "$model_code" -eq 0 && "$tee_code" -eq 0 ]]; then
  printf '%s\n' 'finished' >"$launcher_dir/status.txt"
  exit 0
fi

printf '%s\n' 'failed' >"$launcher_dir/status.txt"
if [[ "$model_code" -ne 0 ]]; then
  exit "$model_code"
fi
exit "$tee_code"
