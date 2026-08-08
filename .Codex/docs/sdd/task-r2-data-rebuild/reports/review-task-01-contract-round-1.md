# R2 数据重建任务 01 修复轮次 1 独立复审

## 结论

- 复审结论：**允许进入服务器目标验收**。
- 原审查的 1 项严重问题和 4 项重要问题均已关闭；未发现新的严重或重要问题。
- 原审查的 3 项建议未纳入本轮修复，当前仍保留，但不阻塞服务器目标验收。
- 本结论只表示实现已具备进入服务器验收的条件，不表示服务器测试已经通过，也不表示正式源实物已经验收。
- A/C 历史提取器仍缺少可读取且哈希匹配的快照；配置与源锁继续明确标记为 `approved_manifest_only_blocked` / `blocked`。服务器验收不得把该状态改写为已核验。

## 复审范围

- 完整读取根规则、`thesis/AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`scripts/AGENTS.md`、远程执行合同和 `.Codex/docs/AGENTS.md`。
- 完整读取原任务简报、修复简报、实现报告、原审查报告和修复报告。
- 只读复核以下实现文件：
  - `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py`
  - `thesis/experiments/llm_probe/configs/r2_protocol_data_v1.yaml`
  - `thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py`
- 未修改生产代码、配置或测试；本报告是本轮唯一新增文件。
- 未联网、未访问服务器、未运行本机 `pytest`、未格式化。

## 严重

### 1. 原子不覆盖发布：已关闭

**复核结果：** 下载目标和三份源锁均复用 `_publish_no_replace`。该原语要求临时文件与目标同目录，通过 `os.link(partial, target)` 原子创建目标；普通文件、有效符号链接和悬空符号链接占用目标名时均不会被覆盖。生产模块不再含 `os.replace`。

**代码证据：**

- `_lexists` 使用 `os.path.lexists`，不会把悬空符号链接误判为不存在：`r2_protocol_contract.py:1976`。
- `_publish_no_replace` 校验同目录和普通临时文件，并将 `FileExistsError` 转换为合同错误：`r2_protocol_contract.py:1980`。
- `_write_stable_file` 与 `resume_official_download` 都调用该原语：`r2_protocol_contract.py:1998`、`r2_protocol_contract.py:2240`。
- 下载发布竞争失败后只清理本方临时文件，不改写竞争方目标：`r2_protocol_contract.py:2241`。

**测试证据：**

- 不同源锁内容保持原文件：`test_write_source_lock_rejects_different_content_and_preserves_all_files`。
- 悬空源锁目标拒绝替换：`test_write_source_lock_rejects_dangling_symlink_without_replacement`。
- 源锁目标并发出现时不覆盖：`test_write_source_lock_concurrent_target_never_overwrites`。
- 下载目标并发出现、普通目标已存在及悬空目标存在均有独立节点。

## 重要

### 1. B 提取器实物核验及 A/C 阻塞语义：已关闭

**复核结果：**

- B 固定为 `verified_snapshot`。实现解析批准的完整历史路径后实际读取 `src/flow_probe/tqh_c2.py`，同时核对 SHA-256 和字节数，并要求来源清单哈希等于批准 profile 的 `extractor_contract_sha256`。
- A/C 固定为 `approved_manifest_only_blocked`。实现不把清单值伪装成实物核验结果，源锁行明确写入 `evidence_status=blocked`。

**实物证据：**

- 当前 B 快照 SHA-256：`c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0`。
- 当前 B 快照大小：`55,523` 字节。
- B 的 `source_checksums.json`、`approved-inputs.json`、生产配置和当前快照四处一致。
- A/C 来源清单仍登记旧快照 SHA-256 `7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617`、大小 `46,140` 字节，与当前 B 快照不同，因此继续阻塞是正确行为。

**代码与测试证据：**

- 冻结模式和 profile 常量：`r2_protocol_contract.py:1078`。
- B 实物核验及 A/C 阻塞锁分支：`r2_protocol_contract.py:1718`。
- 完整源锁测试回读序列化结果，断言 B 为 `verified`、A/C 为 `blocked`：`test_verify_frozen_inputs_returns_complete_source_lock`。
- B 快照单变量变化拒绝：`test_verify_frozen_inputs_rejects_single_layer_change[extractor_snapshot-*]`。

### 2. 完整前缀映射与越界、歧义拒绝：已关闭

**复核结果：** 配置逐字冻结 3 条历史前缀。归一化只接受完整路径组件前缀匹配，未知前缀、组件冒充、Windows/UNC、多个映射命中、`..` 后缀和符号链接越界均被拒绝，不再按任意 `raw` 或 `src` 组件截断。

**代码证据：**

- 映射配置解析和重复前缀拒绝：`r2_protocol_contract.py:610`。
- 完整组件前缀匹配、未知与多重命中拒绝：`r2_protocol_contract.py:1532`。
- 解析后的路径必须位于运行时根内：`r2_protocol_contract.py:1569`。

**独立只读核验：** A/B/C 三份实际 `source_checksums.json` 各 73 行来源记录全部且仅命中一条冻结映射，结果为 `PREFIX_MAP_ALL_OK [73, 73, 73]`。

**测试证据：** 批准前缀、未知组件冒充、Windows/UNC、多重命中、路径穿越和符号链接越界均有独立测试节点。

### 3. 不可续传下载与旁路锁清理：已关闭

**复核结果：**

- 网络截断等短文件保留临时文件和旁路锁，允许 Range 续传。
- 超长文件以及完整文件的 MD5、ZIP、CRC、成员或清单失败调用 `_discard_download_state`，清理临时文件和旁路锁；下一次从零开始。
- 发布前先删除旁路锁。旁路锁删除失败时目标尚未发布，完整临时文件和旁路锁均保留，可在清理条件恢复后重试。
- 旁路锁删除成功后才执行原子不覆盖发布；并发目标出现时竞争方目标保持不变，本方临时文件被清理。

**代码证据：**

- 终态清理：`r2_protocol_contract.py:2086`。
- 超长与完整校验失败分支：`r2_protocol_contract.py:2177`、`r2_protocol_contract.py:2220`、`r2_protocol_contract.py:2227`。
- 旁路锁清理位于目标发布之前：`r2_protocol_contract.py:2235`。

**测试证据：** 完整坏文件失败后从零成功、超长状态清理、旁路锁删除失败时目标未发布、目标并发出现时不覆盖均有独立节点。

### 4. 完整冻结输入成功路径及失败合同：已关闭

**复核结果：** `_build_complete_frozen_tree` 构造并实际经过 11 项旧冻结输入、直接预算校验清单、间接共同候选、TQH A/B/C 批准输入、三份制品清单、每 profile 8 项上游制品、来源清单、原始来源、提取器证据、四尺度 GeNIS ZIP 和代码提交绑定，最后返回并序列化 `SourceLock`。

**覆盖证据：**

- 完整成功路径：`test_verify_frozen_inputs_returns_complete_source_lock`。
- 旧冻结输入、间接候选、批准输入、TQH 制品清单、TQH 制品、TQH 原始来源、B 提取器和 GeNIS 均有单变量失败参数。
- 代码绑定失败有独立节点。
- JSONL 行数变化和来源数量变化已经拆成两个节点。
- 10 秒成员大小及 SHA-256 与 `ZipFile.read` 得到的实际解压字节逐项比较。
- Windows/UNC、CRC、不同内容源锁、并发目标、悬空链接、不可续传清理与重试测试均已补齐。

## 建议

### 1. 嵌套映射仍可修改：保留

`R2ProtocolConfig` 虽为 `frozen=True`，但 `common_units`、`enum_values`、`field_roles`、`semantic_gates`、`tqhc2_profiles`、ns-3 映射和 `information_budgets` 仍包含普通可变映射。本轮简报明确不要求处理，因此不阻塞服务器目标验收。

### 2. 源锁仍只记录 Git `HEAD`：保留

`_current_git_commit` 仍只执行 `git rev-parse HEAD`，没有绑定实际执行的未提交生产文件哈希。本轮简报明确不要求处理；正式签锁前仍需避免把脏工作树中的代码误记为该提交。

### 3. 单模块职责过多：保留

`r2_protocol_contract.py` 当前为 2,258 行，仍同时承担配置解析、旧输入核验、TQH 路径迁移、ZIP 核验、源锁写出和下载状态机。本轮禁止以模块拆分替代最小修复，因此不阻塞服务器目标验收。

## 本地验证

### 已通过

1. 不写缓存 AST 检查：生产代码与测试均可解析；六个公开接口存在；生产代码不含 `os.replace`；`os.link` 发布路径和 6 个关键回归节点存在。
   - 结果：`AST_REVIEW_OK 6 40`，其中 40 为测试函数定义数，不含参数化展开后的节点数。
2. 项目虚拟环境、不写缓存的真实配置只读加载与 B 快照绑定核验。
   - 结果：`B_SNAPSHOT_LOCK_OK c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0 55523`。
3. 项目虚拟环境、不写缓存地核对 A/B/C 三份实际来源清单的完整前缀映射。
   - 结果：`PREFIX_MAP_ALL_OK [73, 73, 73]`。
4. 独立 `shasum -a 256` 和 `wc -c` 与上述 B 快照结果一致。

### 未通过但不构成实现失败

- 系统基础 `python3 -B` 缺少 `PyYAML`，只读导入返回 `ModuleNotFoundError: No module named 'yaml'`。随后使用项目既有 `.venv/bin/python -B` 完成同一只读核验；未安装或修改依赖。

### 未执行

- 未运行本机或服务器 `pytest`。
- 未运行 Black、Ruff、Prettier 或其他格式化工具。
- 未执行服务器实物预检、正式下载、网络请求、物化、提交或推送。

## 服务器验收门禁

允许进入服务器项目根执行目标行为测试：

```bash
uv run --no-sync pytest -q tests/test_r2_protocol_contract.py
```

服务器验收还需遵守以下边界：

- 目标测试必须全部通过后，任务 01 才能标记为行为验收完成。
- 正式 GeNIS、旧冻结输入和 TQH A/B/C 实物预检尚未执行，不能用临时夹具结果替代。
- A/C 提取器继续保持 `blocked`；只有取得 SHA-256 和大小均匹配的历史快照后，才允许另行审查是否解除。
- 本轮用户已取消格式化；格式化不属于本复审结论，也不得据此改写代码。
