
> 请求流 panel_2024.f32（168.5 MiB）超 GitHub 100 MB 限制不入库；由 `platform/eval-bench/gen_panel.py` 按固定种子确定性再生（seed 与元数据见同目录 panel_2024_meta.json），重基准前先运行该脚本。

## HuggingFace 托管（2026-10-22）

大文件已托管至 HF 数据集仓库 `Heehobino/lamda-ch5-eval-benchmark`（含 panel_2024.f32、tabm4_state.safetensors、panel_2024_meta.json），版本化提交：
- panel: `3801db965d68e06940e050f02c66582c854780c3`
- model: `63993fa2294cdef8db7c0e96d99caa4b6cdaf028`
- meta: `4aaf99df041bee1adc5340fd66f0e1d7ba907e69`

新机恢复：`hf download Heehobino/lamda-ch5-eval-benchmark --repo-type dataset --revision <上述哈希> --local-dir data/`（需 `hf auth login`）。
