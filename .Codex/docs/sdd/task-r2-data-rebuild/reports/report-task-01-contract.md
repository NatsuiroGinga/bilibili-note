# R2 数据重建任务 01 实现报告

## 状态

- 任务状态：实现完成，等待独立审查与服务器验收。
- 基准提交：`acdf98ba5cc776f7c19495fc53b1164e916eb33c`。
- 实现范围：合同常量、严格配置加载、冻结输入预检、GeNIS ZIP 预检、官方断点恢复和稳定源锁写出。
- 未启动正式物化、训练、下载或服务器实验。

## 修改文件

1. `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py`
2. `thesis/experiments/llm_probe/configs/r2_protocol_data_v1.yaml`
3. `thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py`
4. `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-01-contract.md`

## 公开接口

- `load_r2_config(path: Path) -> R2ProtocolConfig`
- `verify_frozen_inputs(project_root: Path, external_sources: ExternalSourceRoots, config: R2ProtocolConfig) -> SourceLock`
- `verify_genis_archive(path: Path, spec: GeNISArtifactSpec) -> GeNISArchiveInventory`
- `resume_official_download(spec: GeNISArtifactSpec, destination: Path) -> DownloadReceipt`
- `write_source_lock(lock: SourceLock, output_root: Path) -> None`
- `canonical_json_sha256(value: object) -> str`

## 实现内容

### 配置合同

- 冻结数据版本 `flow_probe_r2_protocol_dataset_v0`、阶段 `theory_selection`、状态 `review_pending` 和发布根。
- 冻结 8 个共同字段的顺序、单位与缺失掩码后缀。
- 冻结记录角色、传输族、协议目标、QUIC 证据和字段角色枚举。
- 冻结共同字段、协议字段、QUIC 聚合及其掩码的角色；`TotBytes`、`TcpRtt`、`SrcWin`、`DstWin` 保持后续硬门禁。
- 冻结 Parquet `version=2.6`、`zstd` 级别 9、禁用字典、启用统计、数据页 1.0 和 65,536 行组。
- 冻结旧制品、TQH A/B/C、批准输入、GeNIS 官方元数据、ns-3 数量与覆盖门槛、A/B/C/D 信息预算。
- 配置加载器逐项拒绝未知字段、绝对逻辑路径、哈希/行数漂移和固定合同变化。

### 源预检与源锁

- 旧冻结制品按固定 SHA-256 核验；共同候选通过已冻结预算校验文件取得自身 SHA-256 和大小，再核对 10,000 行及 `genis=3973`、`tqhc2=3606`、`ns3=2421`。
- TQH A/B/C 分别核对批准输入、制品清单、8 个上游制品、主记录/包表 SHA-256 与行数。
- TQH 的 36 个 PCAP、标签和审计原件按已批准 `source_checksums.json` 逐项核验，并将历史绝对路径重锚定为 `raw/` 或 `src/` 逻辑路径。
- A/C 的历史 `extractor_source` 不与当前源码错误比较；其旧版哈希由已批准来源清单和上游制品清单共同绑定。PCAP、标签和审计原件仍读取实际文件核验。
- 源锁绑定运行时实际 Git 提交、静态配置 SHA-256、旧冻结输入和 GeNIS/TQH 子锁哈希。
- 三份源锁采用规范 JSON、逻辑路径排序和换行结尾；相同内容重复写入逐字节一致，不同内容拒绝覆盖。

### GeNIS ZIP 与恢复

- ZIP 预检核对精确大小、官方 MD5、归档 SHA-256、中央目录、CRC、路径穿越、Windows 绝对路径、符号链接和重复成员。
- 固定核对 5/10/30/60 秒各 11 个 CSV，并记录 10 秒尺度 11 个成员的大小和 SHA-256。
- 恢复接口只接受配置登记的 Zenodo HTTPS 地址。
- 已有临时文件只有在旁路锁的 URL、版本、大小和 MD5 全部一致时才发送 `Range`。
- `206` 必须具有精确匹配的 `Content-Range`；收到完整 `200` 时截断临时文件并重新无 Range 下载。
- 大小、MD5 或 ZIP 验证失败时不发布目标；目标已存在时在请求前拒绝覆盖；成功后使用 `os.replace` 原子发布。

## 测试覆盖

测试文件共定义 22 个节点，覆盖：

- 真实配置冻结值和绝对逻辑路径拒绝。
- 规范 JSON 哈希稳定性与非有限值拒绝。
- 四尺度 GeNIS 清单和 10 秒成员哈希。
- ZIP 大小错误、MD5 错误、路径穿越、符号链接、重复成员和损坏中央目录。
- 临时本地 HTTP 服务上的断点续传、错误 `Content-Range`、完整 `200` 从零重启、响应截断、MD5 错误、已有目标拒绝覆盖、非 HTTPS/非登记 URL、旁路锁不一致和成功原子发布。
- 源锁重复构建逐字节一致、幂等写入和绝对路径拒绝。
- 冻结输入缺失、SHA-256 变化、JSONL 行数或来源数量变化立即失败。

测试代码不会访问公网；本地 HTTP 地址只由测试替换请求传输层，生产接口接收的仍是登记的 Zenodo HTTPS URL。

## 已执行检查

未运行本机 `pytest` 或任何格式工具。仅执行以下不导入项目模块、不生成项目缓存的静态检查：

```bash
python -c 'import ast, pathlib; paths=[pathlib.Path("src/flow_probe/r2_protocol_contract.py"), pathlib.Path("tests/test_r2_protocol_contract.py")]; [ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in paths]; print("AST_OK")'
```

结果：`AST_OK`。

```bash
python -c 'import pathlib, yaml; value=yaml.safe_load(pathlib.Path("configs/r2_protocol_data_v1.yaml").read_text(encoding="utf-8")); assert isinstance(value, dict) and len(value["common_view"]["fields"])==8; assert value["sources"]["genis"]["url"]=="https://zenodo.org/api/records/14919237/files/2-flows.zip/content"; print("YAML_CONTRACT_SHAPE_OK")'
```

结果：`YAML_CONTRACT_SHAPE_OK`。

公开接口存在性检查通过，未发现任务文件产生的 `__pycache__` 或 `.pyc`。

## 未执行与待执行验收

按任务限制，以下命令未在本机执行。应在服务器项目根 `/root/autodl-tmp/thesis/experiments/llm_probe` 依次执行：

```bash
uv run --no-sync black src/flow_probe/r2_protocol_contract.py tests/test_r2_protocol_contract.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_contract.py tests/test_r2_protocol_contract.py
uv run --no-sync pytest -q tests/test_r2_protocol_contract.py
```

正式源预检还需由后续服务器包装器显式提供：

- 项目根。
- 仓库根，用于解析 `raw/` 逻辑来源。
- 服务器 GeNIS 正式归档 `/root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip`。
- 如需覆盖配置逻辑根，则提供 TQH A/B/C 运行时绝对根；绝对根不写入源锁。

## 已知阻塞与局限

- 服务器 GeNIS 文件的实际 MD5、SHA-256 和 10 秒成员清单尚未运行本实现核验。
- 旧冻结制品和 TQH 原件尚未在服务器运行全量预检，因此本轮没有生成 `runs/data-freeze-configs/r2-protocol-v1/` 下的源锁制品。
- `TotBytes` 网络层字节语义尚未由一手实现或逐包复算闭合。
- `TcpRtt`、`SrcWin`、`DstWin` 的单位、缩放和聚合语义尚未闭合。
- 上述四项继续保持 `blocked_pending_semantics`；本任务未猜测、填值或解除门禁。
- 本机未执行测试、Black 或 Ruff，最终行为与格式状态以服务器验收和独立审查为准。

## 范围审计

- 是否触碰白名单外文件：否。
- 是否提交或推送：否。
- 是否访问服务器或公网：否。
- 是否读取本机损坏的 `2-flows.zip`：否。
- 是否发现计划冲突：修订后的简报与落盘计划未发现冲突。
- 工作树存在其他既有无关改动；本任务未修改、暂存、回滚或覆盖这些文件。

## 正式源锁与执行代码锁补齐

日期：2026-08-01

### 当前状态

- 已在 `src/flow_probe/r2_protocol_contract.py` 补齐计划公开接口 `build_execution_code_lock` 与 `verify_execution_code_lock`，并增加严格读取、稳定写出和正式参数入口。
- 执行代码锁固定覆盖 `pyproject.toml`、`uv.lock`、R2 配置、包初始化文件、任务01合同模块、任务03模块和既有 `tqh_c2.py`。少项、多项、重复、未跟踪、符号链接、文件哈希变化、非 40 位提交、全仓脏工作树及 Python/PyArrow 版本变化均在正式运行内失败。
- 正式源预检允许代码位于隔离的干净 Git worktree，旧冻结制品仍从显式 `project_data_root` 只读核验；两类绝对运行路径只进入参数和发布根外回执，不进入源锁。
- `source-lock.json` 新增对 `execution-code-lock.json` 文件 SHA-256 的单向绑定。四份锁先写同文件系统阶段根，完成代码锁回验、A/B/C 提取器状态断言和精确文件集合检查后才整体发布。
- A/C 继续严格保持 `approved_manifest_only_blocked` / `blocked`，B 保持 `verified_snapshot` / `verified`；正式入口把这一状态作为硬断言，不能通过缺省值或人工清单提升。
- 新增正式包装器 `scripts/run_r2_protocol_source_preflight.sh`。磁盘公式、解释器、参数模式、代码锁、完整 GeNIS、216 项非提取器来源、额外文件和符号链接拒绝均融合在同一次正式运行中。
- 本机正式参数为 `runs/launchers/r2-protocol-data-rebuild-v0/local-producer/source-preflight-params.json`，SHA-256 为 `c56a61af920cccd2df1edb90d9db99f1e794f8030c36d03299566bd6bb5cdf2b`。
- `bash -n scripts/run_r2_protocol_source_preflight.sh scripts/run_r2_protocol_tqhc2_handoff.sh` 已执行一次并通过，退出码为 `0`。
- 当前生产文件 SHA-256：`r2_protocol_contract.py` 为 `72588073a0453469f1530b4fbbb0c0f891c7e77420660c93a9bf16f93221182b`，配置为 `0793d00a3b67a20960b32efb33c5a5e45cd5bae04d2e7bb24d5e7cd629c5a935`，源预检包装器为 `9558d7fefb4d46b7b1104f892cd01959685683b00e5cbecb0e1d3cee69d38d43`。这些值将在正式提交后由执行代码锁重新计算并绑定，当前不能代替正式代码锁。

### 未执行与阻塞

- 服务器当前按预期关机，本机尚未取得权威完整 GeNIS 归档；因此尚未运行正式源预检，`source-lock.json` 与 `execution-code-lock.json` 尚未生成。
- 本机已核验损坏的 14,520,320 字节旧归档副本已按授权删除，判坏和清理证据见 `report-r2-source-restore-preflight.md`；后续只允许从服务器权威路径拉取到新的 `official/zenodo-14919237-v1.0.0/` 暂存路径。
- 按用户约束，本轮未运行格式化、Prettier、抽象语法树解析、独立真实导入、独立冒烟、pytest 或重复 Pyright。必要行为断言由后续正式包装器运行直接执行。
- 任务01/03文件仍待形成同一职责单一的正式 Git 提交；提交前不得生成执行代码锁。

## 本机代码提交与执行代码锁

日期：2026-08-03

### 已完成

- 用户确认提交信息后，仅将任务 01/03 的两份生产模块、R2 配置、两份测试和两份包装器共 7 个文件加入提交；未暂存任务 02、Rust、ns-3、文档或其他工作树改动。
- 本地提交为 `527531f2f188de21489311259dbb5fcf4f1731ee`，提交信息为 `feat(r2-data): 冻结源锁与TQH移交合同`，父提交为 `acdf98ba5cc776f7c19495fc53b1164e916eb33c`。`git show --format= --name-only --no-renames HEAD` 核验提交清单恰好为上述 7 个文件；未推送、未改写历史。
- 从该提交创建分离头干净工作树 `/private/tmp/r2-source-code-lock-handoff`。代码锁生成前后，`git status --porcelain=v1 --untracked-files=all` 均无输出，`HEAD` 均为上述 40 位提交。
- 在一次本机代码锁运行内执行 `build_execution_code_lock`、稳定写出、严格重载和 `verify_execution_code_lock`，并断言输出目录只有一个普通文件。锁定 Python `3.10.20`、PyArrow `25.0.0` 和固定的 7 个生产制品，`worktree_clean=true`。
- 发布根外的本机代码锁为 `runs/launchers/r2-protocol-data-rebuild-v0/local-producer/execution-code-lock-527531f2f188de21489311259dbb5fcf4f1731ee/execution-code-lock.json`，大小为 `1,185` 字节，SHA-256 为 `e4cb4f6a6f40e977f7881f99e0419db7e525b7e3f74305b1a5a9f354ebcc4c46`。
- 该本机代码锁只证明提交、干净工作树、运行时版本和逐文件内容已经锁定，不代替正式四锁发布，也不证明尚未运行的测试、格式化或静态检查通过。提交钩子明确提示 `GitPreCommit` 不存在或不可执行，因此没有把额外预提交检查记为通过。

### 新发现的发布根冲突（修复前记录）

- 并行 ns-3 任务于 2026-08-03 11:33 已创建共享正式根 `runs/data-freeze-configs/r2-protocol-v1/`，其中只有 `ns3-config-manifest.jsonl` 与 `ns3-config-manifest.sha256`。本任务没有修改、移动或删除这两项制品。
- 修复前的 `run_formal_source_preflight` 在正式源锁根或其阶段根任一已存在时直接失败。因此即使后续取得完整 GeNIS 权威归档，当时的入口也无法在保留上述 ns-3 制品的同时原子发布 `source-lock.json`、正式 `execution-code-lock.json`、`genis-member-lock.jsonl` 和 `tqhc2-source-lock.jsonl`。
- 该冲突随后纳入任务 01R；修复没有通过删除、移动或改写并行 ns-3 制品绕过门禁。

### 剩余阻塞

- 服务器仍关机，本机正式路径 `raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/2-flows.zip` 仍缺失；尚不能运行完整源预检。
- 正式四锁尚未发布到 `runs/data-freeze-configs/r2-protocol-v1/source-locks-v1/`，发布根外的本机代码锁不能替代它们。
- TQH 规范移交根 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0/` 和正式移交清单仍未生成；build-a/build-b 阶段目录继续保留。
- A/C 历史提取器证据继续保持 `blocked`，未补造、未提升。

## 任务 01R：源锁与 ns-3 共享父目录冲突修复

日期：2026-08-03

### 最小修复

- 源锁专属根从共享父目录改为 `runs/data-freeze-configs/r2-protocol-v1/source-locks-v1`；配置加载器继续将该值与生产常量逐项绑定。
- 阶段根仍由 `source_lock_root.with_name(f"{source_lock_root.name}.partial")` 推导，因此精确为同一父目录下的 `source-locks-v1.partial`。
- 目标根或阶段根事前存在即失败、阶段根精确文件集合检查、同文件系统检查、并发目标复查和 `os.rename` 原子发布逻辑均未放宽。
- 真实配置最小测试新增源锁专属根精确值断言；未新增独立测试入口。
- 修复前只读登记的两个 ns-3 清单 SHA-256 分别为：`ns3-config-manifest.jsonl` 为 `a0efc42ed26c0e4bc2c1622f850f5ee61a20348f29693bafa8008108792be793`，`ns3-config-manifest.sha256` 为 `43bbf0056d66fa6841285a18f426a895d645bd4762908b06e46a98ec4869f5ca`。

### 本轮检查边界

- 按任务 01R 限制，未运行测试驱动开发、格式化、Pyright、pytest、独立冒烟、服务器同步或正式源预检。
- 静态人工核对确认配置常量与 YAML 值一致，现有阶段根推导得到 `source-locks-v1.partial`，源锁专属根覆盖拒绝和原子发布分支保持不变。
- 本轮不提交；旧提交 `527531f2f188de21489311259dbb5fcf4f1731ee` 和旧代码锁继续作为历史证据。修复后必须在用户重新授权提交后生成新提交，并从新提交的干净工作树重建执行代码锁。

### 任务 03 消费路径同步

- 扩展白名单后，任务 03 消费者 `src/flow_probe/r2_protocol_tqhc2.py` 的固定源锁根和正式 `tqhc2-handoff-params.json` 均同步到 `source-locks-v1`。
- 既有任务 03 合同测试直接读取正式参数，断言其 `source_lock_root` 精确等于专属根；移交数据、标签、四锁文件集合、拒绝覆盖和原子发布逻辑均未改变。

### 精确运行时验收动作

1. 在正式源预检前，枚举 `runs/data-freeze-configs/r2-protocol-v1/` 的一级普通文件，断言恰好为 `ns3-config-manifest.jsonl` 与 `ns3-config-manifest.sha256`，并逐项复核上述 SHA-256。
2. 断言 `runs/data-freeze-configs/r2-protocol-v1/source-locks-v1` 与同级 `source-locks-v1.partial` 均不存在；任一已存在即停止，不删除、不覆盖。
3. 用户授权新提交后，从该新提交创建干净工作树，更新正式参数中的 `project_root`，再执行 `bash scripts/run_r2_protocol_source_preflight.sh runs/launchers/r2-protocol-data-rebuild-v0/local-producer/source-preflight-params.json`。该动作同时执行真实配置加载、完整源预检、阶段根四锁精确集合核验和原子发布。
4. 成功后断言专属根恰好包含 `execution-code-lock.json`、`genis-member-lock.jsonl`、`source-lock.json` 与 `tqhc2-source-lock.jsonl` 四个普通文件，且阶段根不存在。
5. 再次复核父目录两个 ns-3 清单的文件名、大小和 SHA-256 与步骤 1 完全一致；失败运行必须保留失败状态与启动日志，不得清理或覆盖既有制品。
