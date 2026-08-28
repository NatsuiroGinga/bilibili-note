# CUDA-RWKV 自身资格门证据笔记

## 冻结依据

- 方案提交：`334ed1d19827ea5eb791f84900a020916e11354a`。
- 官方固定提交：`952102498e9ed367ea0a59ee64106916d474d30f`。
- 官方原件：`vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cpp`、`vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cu`。
- 官方原件 SHA-256：C++ 为 `f6781adacbe0ab8638b666e0bd49098e262a861b7cc95fb1735ab54a43d82628`，CUDA 为 `a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb`。
- 许可证：Apache-2.0，许可证文件 SHA-256 为 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`。
- 小型容量：`B=2`、`T=128`、`C=112`、头大小 `16`、头数 `7`、低秩维 `8`、分块长度 `16`。

## 源码核验

- 官方 CUDA 前向核在每个批次和头开始时把递归状态置零，随后按时间步递推，因此块首状态重置由计算核实现。
- 官方 CUDA 核没有掩码参数；全零掩码和补零语义必须由外层独立模型处理。
- 官方反向核显式生成 `dr,dw,dk,dv,da,db` 六个 BF16 梯度张量。
- 现有独立加载接口在模块导入时不编译，仅在显式加载或调用时核验目标环境和构建扩展。

## 第三方接口核验

### PyTorch 版本

- 项目声明：`torch>=2.8,<3`。
- 冻结目标环境：`torch==2.13.0+cu130`、CUDA `13.0`、计算能力 `12.0`。

### 官方文档来源

- `https://docs.pytorch.org/docs/main/cpp_extension.html`
  - `torch.utils.cpp_extension.load` 接收 `name`、`sources`、`extra_cflags`、`extra_cuda_cflags`、`build_directory`、`verbose`、`with_cuda`、`is_python_module` 等参数。
  - `build_directory` 可把 Ninja 构建文件和动态库固定到持久目录；`is_python_module=False` 会把动态库加载进进程而不要求 Python 模块绑定。
  - `TORCH_CUDA_ARCH_LIST` 可显式限定目标计算能力。
- `https://docs.pytorch.org/docs/stable/notes/randomness.html`
  - `torch.use_deterministic_algorithms(True)` 会为已知算子选择确定性实现或在无确定性实现时抛错；该设置本身不能替代同进程逐位复核。
- `https://docs.pytorch.org/docs/stable/generated/torch.cuda.is_bf16_supported.html`
  - `torch.cuda.is_bf16_supported()` 返回当前设备是否支持 BF16。
- `https://docs.pytorch.org/docs/stable/cuda.html`
  - `memory_allocated`、`memory_reserved`、`max_memory_allocated`、`max_memory_reserved` 分别报告当前与峰值的已分配和保留显存。

### 采用接口

- 继续使用目标后端已核验的 `torch.utils.cpp_extension.load(..., extra_cuda_cflags=..., is_python_module=False)` 路径。
- 资格工具使用 `torch.use_deterministic_algorithms(True, warn_only=False)`，并直接用 `torch.equal` 比较两次输出、损失和六梯度。
- 显存收据记录当前和峰值两组 allocated/reserved 指标。

## 资格门判据

- 六输入全部满足 `[2,128,112]`、BF16、CUDA、连续、可求梯度。
- 两次运行输出、标量损失和六梯度逐位相等。
- 输出、损失和六梯度全部有限；每个梯度张量至少一个元素非零。
- 六个单张量微扰分别使输出或损失至少一个发生变化，且变化结果有限。
- 有效前缀输出不受尾部补零影响；全零掩码的输出和损失贡献严格为零。
- 输入投影、CUDA 块、输出头的 FP32 参数均有限，且每个模块至少一个参数在单次优化步后变化。
- 完成收据必须绑定配置、工具、启动器、官方源、派生注册源、扩展二进制和环境身份。

## 当前边界

- 未访问服务器。
- 未运行 CUDA 编译、前向、反向或优化步。
- 未读取任何数据。
- 未创建 SwanLab 身份。
- 当前科学状态：实验待证。

## 本地静态验收

- `uv run --no-sync python -m py_compile tools/ch3_rwkv_cuda_self_gate.py`：通过。
- 使用 `importlib.util` 导入工具：通过；未初始化 CUDA，未编译扩展。
- `--help`：通过，列出 `--validate-config`、`--print-contract`、`--run`。
- `--validate-config`：通过，返回 `config_valid=true`。
- `--print-contract`：通过，确认外部记录读取为假、跟踪身份创建为假、优化更新次数为一。
- `bash -n scripts/remote_launchers/run_ch3_rwkv_cuda_self_gate_v1.sh`：通过。
- 生产配置、工具和启动器禁止内容扫描：零命中。
- 官方许可证、C++、CUDA 原件 SHA-256 分别为 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`、`f6781adacbe0ab8638b666e0bd49098e262a861b7cc95fb1735ab54a43d82628`、`a879dd478457290ebe793a10fcd0c1b93db1e1afb9d51ff8f8f1245a0146bbfb`，与清单一致。
- 供应商四文件相对当前 `HEAD` 无差异；派生 C++ 与官方 C++ 的差异只包含文件头说明、格式和专用注册命名空间，CUDA 文件无派生副本且未修改。
- 工具与启动器对九个身份文件生成的清单 SHA-256 算法实测一致。

## B76 真实前置失败

- 真实前置检查退出码：`69`。
- 失败位置：启动器外层 `validate_commands` 的 `command -v nvcc`，早于 `mkdir`、`record_identity` 和持久工作进程。
- 运行身份：未创建新的远端运行身份，可继续使用 `ch3-rwkv-cuda-self-gate-v1`。
- 只读环境证据：PyTorch `2.13.0+cu130`、`torch.version.cuda=13.0`、`CUDA_HOME=/usr/local/cuda`。
- 工具链证据：`/usr/local/cuda/bin/nvcc` 存在，报告 CUDA `13.0`。
- 根因假设：CUDA 工具链完整，但环境激活后的非交互 PATH 没有包含冻结 `CUDA_HOME/bin`；因此 `command -v nvcc` 失败，不是工具链缺失或 CUDA 版本不符。
- 单变量修复：配置新增并冻结 `cuda_home=/usr/local/cuda`；启动器在命令门前导出冻结 CUDA 环境；工具对环境变量和 `nvcc` 解析路径作双重断言。
- 未改变：官方核、供应商摘要、`B/T/C/头大小/低秩维`、精度、固定种子、微扰、前缀、优化器、测量次数、路径和 gate_id。
- 修复后本地静态检查：`py_compile`、延迟导入、帮助、配置、静态合同、`bash -n` 和 `git diff --check` 均通过。
- 当前边界：本代理未重新访问服务器；修复后的真实 B76 前置检查尚未执行。

## PyTorch 技能适配

- 已读取 `pytorch-patterns` 的确定性、显式形状、`train/eval`、`zero_grad(set_to_none=True)` 和显存意识条目。
- 技能默认建议设备无关实现，但本资格门的冻结对象就是 `sm_120` 官方 CUDA 核。这里按更近层实验合同采用 CUDA 硬门，缺少 CUDA、BF16 或冻结版本时直接失败，不提供 CPU 路径。
- 本门使用固定种子、`torch.use_deterministic_algorithms(True, warn_only=False)`、`model.eval()` 掩码检查、`model.train()` 单步更新和 FP32 参数断言。
