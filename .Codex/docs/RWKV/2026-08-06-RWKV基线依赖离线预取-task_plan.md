# RWKV 基线依赖服务器预取计划

## 目标

在不启动训练、不下载无关预训练权重的前提下，取得旧服务器的环境收据，直接在旧服务器准备与其兼容的基线源码、依赖清单和可校验制品。

## 阶段

- [x] 阶段 1：只读核验旧服务器身份、架构、系统、磁盘、Python、uv、CUDA、PyTorch 与编译工具。
- [x] 阶段 2：冻结 HGB、XGBoost、GRU、TCN、因果 Transformer、TimesNet、Mamba 和 RWKV-7 的源码与依赖边界。
- [x] 阶段 3：直接在旧服务器下载冻结源码快照、源代码包和匹配 Linux 的二进制制品，生成大小与 SHA-256 清单。
- [x] 阶段 4：核对服务端制品完整性、来源、许可证、磁盘占用和 SHA-256。
- [x] 阶段 5：通过白名单 `rsync` 将已验收制品和清单回收本机，复核双端 SHA-256。
- [x] 阶段 6：记录可离线安装项、必须在服务器编译项、未下载项及后续 `uv` 安装命令。

## 冻结边界

- 不下载 RWKV、Mamba、Transformer 或其他基线的预训练权重。
- 数值序列基线全部从头训练；预取对象仅为源码和运行依赖。
- 用户已明确允许本批基线依赖直接在旧服务器下载，不再使用本机中转。
- Mamba 的 CUDA 扩展必须匹配旧服务器的 Python、PyTorch、CUDA、编译器和系统 ABI。
- 服务器已有 PyTorch 2.13.0+cu130，不重复下载 PyTorch。
- 下载目录不得包含凭据、预训练权重、原始数据或现有运行结果。
- 服务端制品通过来源、大小和 SHA-256 验收后必须回收本机；回收禁止 `--delete`，不得复制服务器 `.venv` 或临时构建缓存。

## 预期制品

- 环境收据：`.Codex/docs/RWKV/2026-08-06-旧服务器基线环境收据.md`
- 本地备份根：`thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps/`
- 服务端依赖根：`/root/autodl-tmp/thesis/experiments/llm_probe/artifacts/rwkv-baseline-deps/`
- 制品清单：`manifest.sha256` 与 `manifest.json`

## 当前状态

**已完成。** 4 个官方源码快照、21 个离线包、环境审计、许可证、`manifest.json`、`manifest.sha256` 和压缩包已从旧服务器回收本机并通过双端 SHA-256 核验。详细结果见[服务器预取与本机备份报告](2026-08-06-RWKV基线依赖服务器预取与本机备份报告.md)。正式 `.venv` 已有 HGB、XGBoost 与通用 PyTorch 序列基线核心依赖；Mamba、`causal-conv1d` 和官方 RWKV CUDA 核仍因 `nvcc` 缺失而禁止编译。
