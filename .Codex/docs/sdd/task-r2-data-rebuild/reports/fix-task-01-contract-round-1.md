# R2 数据重建任务 01 修复轮次 1 报告

## 结论

- 状态：已按修复简报完成 1 项严重问题和 4 项重要问题的最小修复。
- 修改范围严格限于白名单中的生产代码、冻结配置、目标测试和本报告。
- 未处理原审查报告中的 3 项建议，未拆分模块，六个公开接口名称、参数和冻结版本值保持不变。
- 仅完成不写缓存的 AST、YAML 和白名单静态自审；未运行本机或服务器 `pytest`，因此行为测试仍待服务器验收。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py`
- `thesis/experiments/llm_probe/configs/r2_protocol_data_v1.yaml`
- `thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py`
- `.Codex/docs/sdd/task-r2-data-rebuild/reports/fix-task-01-contract-round-1.md`

## 严重问题修复

### 1. 下载目标和源锁原子不覆盖发布

修改位置：

- 生产代码新增 `_lexists` 和 `_publish_no_replace`。
- `_publish_no_replace` 强制临时文件与目标位于同一目录，以 `os.link` 原子创建目标；目标目录项已存在时转换为 `R2ProtocolContractError`，不再调用具有覆盖语义的 `os.replace`。
- `_write_stable_file` 与 `resume_official_download` 共同复用 `_publish_no_replace`。
- 所有存在性判断覆盖普通文件、有效符号链接和悬空符号链接。
- 原子链接成功后的临时硬链接删除失败不再把已成功发布报告为接口失败。

新增或加强测试节点：

- `test_write_source_lock_rejects_different_content_and_preserves_all_files`
- `test_write_source_lock_rejects_dangling_symlink_without_replacement`
- `test_write_source_lock_concurrent_target_never_overwrites`
- `test_resume_official_download_rejects_existing_destination_without_request`
- `test_resume_official_download_rejects_dangling_destination_symlink`
- `test_resume_official_download_concurrent_target_never_overwrites`

这些节点分别检查普通既有内容、不同源锁内容、悬空符号链接和检查后并发出现目标，均要求原内容保持不变。

## 重要问题修复

### 1. 提取器证据不得无条件抄录清单

修改位置：

- 配置为每个 TQH profile 新增 `extractor_evidence_mode`。
- B 冻结为 `verified_snapshot`；生产核验通过历史路径映射定位 `src/flow_probe/tqh_c2.py`，调用 `_verify_file` 同时核对实际 SHA-256 和字节数。
- A/C 冻结为 `approved_manifest_only_blocked`；源锁行显式写入 `evidence_mode=approved_manifest_only_blocked` 和 `evidence_status=blocked`，不再伪装成实物已核验。
- B 源锁行显式写入 `evidence_mode=verified_snapshot` 和 `evidence_status=verified`。
- 每个提取器来源行的 SHA-256 还必须等于对应批准 profile 的 `extractor_contract_sha256`。

证据核对：

- 本地 B 批准快照 `src/flow_probe/tqh_c2.py` 的实际大小为 `55,523` 字节。
- 实际 SHA-256 为 `c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0`，与批准清单一致。
- 未找到能够证明 A/C 旧哈希 `7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617` 的历史提取器快照，因此没有解除 A/C 阻塞。

测试节点：

- `test_real_config_freezes_complete_r2_contract`
- `test_verify_frozen_inputs_returns_complete_source_lock`
- `test_verify_frozen_inputs_rejects_single_layer_change[extractor_snapshot-*]`

完整源锁测试同时回读 `tqhc2-source-lock.jsonl`，确认 B 为已核验、A/C 为阻塞。

### 2. 历史路径必须按冻结完整前缀重锚定

修改位置：

- 配置新增 3 条 `historical_path_mappings`，逐字冻结实际清单使用的两个原始数据前缀和一个提取器前缀：
  - `/Users/bilibili/personal/note/raw` → `repository:raw`
  - `../../../raw` → `repository:raw`
  - `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src` → `project:src`
- `_normalise_tqh_source_path` 只接受完整路径组件前缀匹配，拒绝未知前缀、多重命中、非规范路径、Windows/UNC 路径和包含 `..` 的重锚定后缀。
- `_resolve_tqh_source_path` 在访问文件前解析路径并确认结果仍位于运行时 `repository_root` 或 `project_root` 内，符号链接越界同样失败。
- 不再按任意 `raw` 或 `src` 路径组件截断。

测试节点：

- `test_tqh_historical_paths_require_approved_complete_prefixes`
- `test_tqh_historical_paths_reject_unknown_component_impostors_and_windows_paths`
- `test_tqh_historical_paths_reject_multiple_matches_and_traversal`
- `test_tqh_reanchored_path_rejects_symlink_escape`

### 3. 下载状态机区分可续传截断和不可续传终态

修改位置：

- 新增 `_discard_download_state`，用于清理超长临时文件以及完整文件 MD5、ZIP、CRC、成员或清单核验失败后的临时文件和旁路锁。
- 下载结果短于官方大小时继续保留临时文件和旁路锁，允许后续 Range 续传。
- 临时文件超过官方大小时立即清理，下一次从零开始。
- 完整临时文件进入 `verify_genis_archive` 后，只要合同核验失败就清理不可续传状态。
- 旁路锁改为在目标发布前删除；若删除失败，接口报错时目标尚未发布，完整临时文件与旁路锁仍可重试。
- 旁路锁删除成功后才调用统一原子不覆盖发布原语；若并发目标出现，保留竞争方目标并清理失去旁路锁的本方临时文件。

测试节点：

- `test_resume_official_download_rejects_size_error_without_publish`
- `test_resume_official_download_rejects_md5_error_without_publish`
- `test_resume_official_download_discards_bad_complete_file_then_retries_from_zero`
- `test_resume_official_download_discards_oversized_terminal_state`
- `test_resume_official_download_sidecar_cleanup_failure_precedes_publish`
- `test_resume_official_download_concurrent_target_never_overwrites`

### 4. 补齐完整冻结输入与明确失败合同

修改位置：

- 新增 `_build_complete_frozen_tree` 临时源树夹具，构造并实际经过：
  - 全部 11 项旧冻结输入；
  - 直接绑定的预算校验清单；
  - 由预算清单间接绑定的共同候选 JSONL；
  - TQH A/B/C 批准输入、制品清单、8 项上游制品、来源清单、原始来源和提取器证据；
  - GeNIS 四尺度 ZIP；
  - 代码提交绑定；
  - `SourceLock` 返回和三份源锁写出。
- `test_verify_frozen_inputs_rejects_single_layer_change` 对旧冻结输入、间接候选、批准输入、TQH 制品清单、TQH 制品、TQH 原始来源、B 提取器快照和 GeNIS 分别执行单变量失败检查。
- `test_verify_frozen_inputs_rejects_code_binding_failure` 单独覆盖代码绑定失败。
- JSONL 行数变化和来源数量变化拆分为两个独立节点，不再使用合并正则掩盖先失败分支。
- GeNIS 成功测试通过 `ZipFile.open/read` 得到实际解压字节，逐成员核对 10 秒 CSV 的字节数和 SHA-256。
- 新增 ZIP Windows/UNC 绝对路径和 CRC 损坏测试。
- 新增不同内容源锁不覆盖、并发不覆盖、悬空符号链接、不可续传清理和重试测试。

关键测试节点：

- `test_verify_frozen_inputs_returns_complete_source_lock`
- `test_verify_frozen_inputs_rejects_single_layer_change`
- `test_verify_frozen_inputs_rejects_code_binding_failure`
- `test_verify_frozen_inputs_rejects_frozen_jsonl_row_count_change`
- `test_verify_frozen_inputs_rejects_frozen_jsonl_source_count_change`
- `test_verify_genis_archive_records_four_scales_and_ten_second_hashes`
- `test_verify_genis_archive_rejects_windows_and_unc_absolute_paths`
- `test_verify_genis_archive_rejects_crc_damage`

## 静态检查

已执行且通过：

1. 不写缓存 AST 检查：解析生产代码和测试，核对六个公开接口参数未变，确认生产代码不含 `os.replace`，并确认关键回归节点存在。
   - 结果：`AST_OK 6 52`
2. 不写缓存 YAML 检查：解析生产配置，核对 3 条历史路径映射，以及 A/C 阻塞、B 实物核验三项证据模式。
   - 结果：`YAML_OK 8 3`
3. 白名单静态搜索：生产代码中未发现 `os.replace` 或基于 `Path.exists()` 的发布判断；下载目标和源锁均调用 `_publish_no_replace`。
4. 白名单状态检查：三个实现文件仍是上一轮开始的新文件；本报告已落盘，但 `.Codex/` 按仓库 `.gitignore` 规则不显示在普通 `git status` 中。

## 未执行项

- 未运行本机 `pytest`。
- 未运行 Black、Ruff、Prettier、`git diff --check` 或其他格式化命令。
- 未执行服务器命令、服务器测试或服务器实物验收。
- 未执行任何网络命令。
- 未提交、未推送。

待服务器执行的目标行为测试：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run pytest -q tests/test_r2_protocol_contract.py
```

## 遗留阻塞与风险

- A/C 历史提取器只有已批准清单证据，没有可读取且哈希匹配的历史快照；配置和源锁继续显式标记为阻塞，不能进入声称 A/C 提取器实物已核验的正式签锁状态。
- 本轮未运行行为测试。AST/YAML 通过只能证明语法、结构和冻结字段静态一致，不能证明并发文件系统、HTTP 状态机、ZIP CRC 和完整临时源树测试在服务器环境中通过。
- 正式 GeNIS、旧冻结输入和 TQH A/B/C 服务器实物核验仍未执行。

## 范围自审

- 未处理嵌套映射不可变、脏工作树代码绑定和模块拆分三项建议。
- 未修改六个公开接口签名、数据集版本、阶段、状态、发布根、源锁根、官方 GeNIS 元数据或其余冻结科学合同。
- 未修改白名单外文件。
