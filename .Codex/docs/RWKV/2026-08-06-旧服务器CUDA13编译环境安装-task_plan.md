# 旧服务器 CUDA 13.0 编译环境安装计划

## 目标

在不安装 CUDA 元包、不替换 NVIDIA 驱动、不启动训练的前提下，为旧 GPU 服务器中的 PyTorch `cu130` 环境补齐 CUDA 13.0 最小编译工具链，并判定 RWKV/Mamba CUDA 编译前置是否解除。

## 边界

- `cuda-compiler-13-0` 与 `cuda-libraries-dev-13-0` 已为服务器镜像预装包，停止任何 CUDA APT 安装，不新增 NVIDIA 软件源。
- `ninja` 优先使用正式 `.venv` 的已有 `1.13.0` 软件包；只有虚拟环境制品不存在时才允许安装 Ubuntu `ninja-build`。
- 禁止安装 `cuda`、`cuda-13-0`、任何驱动包或 Ubuntu `nvidia-cuda-toolkit`；禁止执行 `apt upgrade`。
- 不修改模型、数据或训练代码，不启动训练。
- 官方 CUDA 13.0 软件包不可用时立即停止，不使用非官方回退方案。

## 阶段

- [x] 阶段 1：读取 RWKV 恢复文档、实验规则与远程执行合同。
- [x] 阶段 2：只读核验 Ubuntu、驱动、PyTorch CUDA、现有 `nvcc`、GPU 计算能力和磁盘。
- [x] 阶段 3：回滚指令到达前已完成的临时系统源、系统 profile 和多余 `ninja-build`，确保 CUDA 预装包与驱动不变。
- [x] 阶段 4：验证 `CUDA_HOME`、`nvcc`、PyTorch CUDA、GPU 计算能力和 `torch.utils.cpp_extension.CUDA_HOME`。
- [x] 阶段 5：执行一个独立的最小 CUDA 编译与运行验证，不导入 RWKV/Mamba 模型代码。
- [x] 阶段 6：写入安装报告，更新 RWKV 路线总控的确定环境状态。

## 验收条件

- PyTorch `torch.version.cuda` 仍为 `13.0`，GPU 可见且计算能力可读。
- `/usr/local/cuda-13.0/bin/nvcc --version` 成功，且 `CUDA_HOME=/usr/local/cuda-13.0`。
- `torch.utils.cpp_extension.CUDA_HOME` 解析为 `/usr/local/cuda-13.0`。
- 最小 CUDA 源码能编译、链接并在 GPU 上运行成功。
- 安装前后磁盘变化可追溯，限定包版本可追溯，驱动版本未变。

## 错误记录

- 首次读取 `RWKV路线总控.md` 时返回文件不存在；随后使用已确认的 `fd` 列出目录后发现文件已出现，再次读取成功。该现象与其他代理并发写入一致，未做回滚或覆盖。
- 首次未提权的后续 SSH 盘点被本机沙箱拒绝；立即改为经批准的 `expect /tmp/gpu-exec.exp` 统一入口，没有产生远程改动。
- 控制器“不配置 NVIDIA 仓库、不写系统 profile”的新边界在受控安装已结束后到达；当时已临时写入官方源、签名文件、APT 固定文件与 `/etc/profile.d/cuda-13-0.sh`，并新增 `ninja-build=1.10.1-1`，但未安装或升级 CUDA/驱动包。已停止后续 CUDA APT 操作，开始精确回滚自身变更。
- 本机 JSON 终检首次误用 `jq -e empty`，由于 `empty` 不产生输出而返回状态 4；改用 `jq -e .` 检查同一组文件后全部通过，未修改制品。

## 当前状态

**已完成**：临时系统变更已回滚，项目级 CUDA 环境、`sm_120` 编译和 PyTorch 路径验证通过，报告与制品已回收本机。
