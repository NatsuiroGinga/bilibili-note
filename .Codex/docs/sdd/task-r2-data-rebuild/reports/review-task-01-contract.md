# R2 数据重建任务 01 独立代码审查

## 结论

- 审查结论：**请求修改**。
- 发现数量：严重 1 项、重要 4 项、建议 3 项。
- 当前不能判定“可以进入服务器目标测试”。应先修复全部严重和重要问题、补齐精确回归测试，再执行简报规定的服务器格式化、静态检查和目标测试。
- 用户取消本轮格式化属于既定边界，不是实现缺陷。服务器行为测试尚未运行，仅作为残余风险记录。

## 审查范围

- 已只读审查任务 01 计划、实现简报、生产配置、生产代码、测试和实现报告。
- 未修改任何审查对象，未读取本机 GeNIS ZIP，未运行本机 `pytest`、格式化、服务器或网络命令。
- 本报告是本轮唯一新建文件。

## 严重

### 1. “拒绝覆盖”检查与 `os.replace` 分离，仍可覆盖并发出现或悬空符号链接形式的既有目标

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1814`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1826`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1828`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2018`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2020`。

**影响：** 下载目标或源锁目标如果在存在性检查之后、`os.replace` 之前由其他进程创建，现有文件会被静默替换。`Path.exists()` 对悬空符号链接返回假，也会直接进入替换路径。这违反“目标拒绝覆盖”和“不同内容拒绝覆盖”，并存在破坏既有数据或冻结锁的风险。

**证据：** 两条发布路径都先调用 `exists()`，随后调用具有覆盖语义的 `os.replace`；这两个动作不是一个原子的不覆盖操作。成功测试只检查单进程最终结果，没有制造检查与发布之间的目标竞争。

**最小修复：** 抽取统一的同目录、不覆盖发布原语。临时文件完成写入并 `fsync` 后，使用能在目标已存在时原子失败的操作，例如同一文件系统内先 `os.link(partial, target)`、成功后再删除临时名，并把 `EEXIST` 转换为 `R2ProtocolContractError`；不得使用仍会覆盖目标的普通重命名。下载和三份源锁都复用该原语，并增加并发出现目标、悬空符号链接和既有内容保持不变的回归测试。

## 重要

### 1. `extractor_source` 对 A/B/C 三个配置都只抄录清单值，没有实际读取或核验来源文件

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1562`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1576`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1584`。

**影响：** 提取器源文件缺失、被修改或根本不可访问时，`verify_frozen_inputs` 仍会签发包含其哈希和大小的源锁。该分支适用于 A、B、C 全部配置，并非注释所述仅处理 A/C 历史版本，因而没有满足“TQH A/B/C 上游逐项真实核验”的合同。

**证据：** `role == "extractor_source"` 时直接用来源清单中的 `digest` 和 `size_bytes` 构造 `SourceArtifactLock`，没有解析 `actual_path`，也没有调用 `_verify_file`。固定哈希可以证明来源清单未变化，但不能证明清单声明的源文件当前存在且字节匹配。

**最小修复：** 为 A/B/C 保留可读取的批准提取器快照，并与其他来源一样调用 `_verify_file`。若 A/C 历史快照确实不存在，应把“仅由批准清单证明”的模式显式冻结到配置和锁中，并保持阻塞状态；不得用普通已核验锁表示。至少 B 配置不能沿用 A/C 的历史例外。

### 2. 历史路径重锚定按任意 `raw` 或 `src` 路径组件截断，可能核验与批准路径身份不同的文件

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1436`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1439`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1444`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1591`。

**影响：** 例如任意绝对路径 `/unapproved/prefix/raw/x` 都会被改写为当前仓库的 `raw/x`。函数没有验证原路径属于批准的历史根，也没有拒绝多重或歧义组件，因此源锁可能把当前仓库中的同哈希文件冒充为批准路径所指来源，削弱路径级来源证明。

**证据：** `_normalise_tqh_source_path` 使用首次 `parts.index("raw")` 或 `parts.index("src")`，直接丢弃此前全部组件；之后只核验重锚定后的当前文件。批准清单的固定哈希约束了原字符串，却没有证明这种截断映射本身正确。

**最小修复：** 在冻结配置中登记允许的历史绝对前缀到逻辑根的明确映射，只接受完整前缀匹配；拒绝未知前缀、多重命中和歧义路径。重锚定后再验证路径仍位于运行时 `repository_root` 或 `project_root` 内，并为越界、未知前缀和冒充路径增加测试。

### 3. 完整临时文件校验失败会形成永久失败状态，发布后旁路锁清理失败又会出现“已发布但接口报错”

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1970`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2013`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2017`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2020`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:2024`。

**影响：** 当完整临时文件的 MD5、ZIP 中央目录、CRC 或清单校验失败时，临时文件和旁路锁不会清理。下一次调用发现 `resumed_from == size_bytes` 后不再下载，只会重复同一校验失败，必须人工删除。反向场景中，目标已经发布后若旁路锁删除失败，函数会抛错；调用方看到失败，但目标已经存在，重试又会被“拒绝覆盖”阻断。

**证据：** 下载大小满足时直接进入 `verify_genis_archive`，异常路径没有终态清理；发布顺序则是先 `os.replace`，再删除旁路锁并把清理错误升级为合同错误。测试 `/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:368` 只断言错误目标未发布，没有断言完整坏临时文件被清理及下一次调用能够重新下载。

**最小修复：** 明确下载状态机不变量：网络截断等仍可续传的未完整文件可以保留；超长文件、完整文件 MD5/ZIP/CRC/清单失败等不可续传终态必须原子清理临时文件和旁路锁，或标记为无效并在下一次从零开始。调整发布与旁路锁清理顺序，保证函数抛异常时目标尚未发布，或保证目标已发布时返回成功且把残留清理作为可重试状态。增加“坏完整文件失败后第二次成功下载”和“旁路锁删除失败”的测试。

### 4. 22 个测试节点没有覆盖核心冻结输入成功路径和多项明确失败合同

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:219`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:352`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:452`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:491`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_r2_protocol_contract.py:513`。

**影响：** 当前测试即使全部通过，也不能证明 TQH A/B/C 批准输入、8 个上游制品、原始来源、主记录和包表行数、间接预算清单及 GeNIS 被完整核验。它也不能拦截上述提取器漏验、重锚定冒充、覆盖竞争或终态恢复缺陷，因而不足以充当任务 01 的服务器验收门禁。

**证据：** `verify_frozen_inputs` 只有两个早期失败测试，没有一次构造完整输入并成功返回 `SourceLock`；这两个测试都会在进入 TQH 和 GeNIS 核验前失败。名为“行数变化”的测试同时把两行 `genis` 与期望一行 `genis` 比较，并允许匹配“来源数量变化|行数变化”，实际没有隔离行数分支。ZIP 成功测试只断言成员数量、尺度和路径前缀，没有把记录的大小、SHA-256 与实际解压字节比较；还缺少 Windows 绝对路径、CRC 损坏、不同内容源锁拒绝覆盖和下载终态清理测试。

**最小修复：** 增加一个完整临时源树的成功测试，实际经过旧冻结输入、间接预算清单、A/B/C、GeNIS 和 Git 提交绑定并检查返回锁；随后分别对每一层做单变量失败测试。把 JSONL 行数与来源数量拆成两个节点；直接用 `archive.open` 的解压字节核对 10 秒成员大小和 SHA-256；补充 Windows/UNC 路径、CRC、不同锁内容、并发不覆盖、不可续传失败清理与重试节点。真实生产 YAML 的直接加载测试应继续保留。

## 建议

### 1. `frozen=True` 没有冻结嵌套映射，加载后的合同仍可被调用方原地修改

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:243`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:255`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:273`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1274`。

**影响：** 数据类禁止属性重新赋值，但 `common_units`、`enum_values`、`field_roles`、`tqhc2_profiles`、ns-3 映射和嵌套信息预算实际仍是普通 `dict`/`list`。后续任务可能在通过严格加载后意外改变冻结合同。

**证据：** 构造配置时直接保存字典，并对信息预算只做浅层 `dict(...)` 复制；没有递归不可变转换。

**最小修复：** 在加载边界递归转换为不可变映射和元组，或只向下游暴露不可变快照；增加“加载后不可修改”的接口测试。

### 2. 正式源锁只记录 `HEAD`，不能证明脏工作树中实际执行的生产代码

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1454`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1792`。

**影响：** 通过同步未提交文件运行时，源锁中的 `code_commit` 仍指向旧 `HEAD`。配置哈希只能绑定配置，不能绑定本模块及后续物化代码，可能让来源锁看似可复现但实际代码不属于所记提交。

**证据：** `_current_git_commit` 只执行 `git rev-parse HEAD`，没有检查相关文件是否与该提交一致，也没有记录代码文件哈希。

**最小修复：** 正式签锁前仅检查相关代码文件相对 `HEAD` 是否干净，或把实际执行代码的规范文件清单及 SHA-256 写入锁；不要因仓库中无关用户改动而要求整个工作树干净。

### 3. 单模块同时承担严格模式、旧制品核验、TQH 来源迁移、ZIP 安全和网络恢复，已增加回归修复耦合

**位置：** `/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1159`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1467`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1645`、`/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py:1947`。

**影响：** 2,035 行模块中的文件系统发布和网络恢复已共享私有写入逻辑，当前覆盖缺陷也横跨两类职责。后续任务继续复用时，局部修复容易影响不相关合同。

**证据：** 同一文件包含配置解析、精确常量镜像、Parquet/JSONL 核验、历史路径重锚定、ZIP 全量读取、源锁序列化和 HTTP Range 状态机。

**最小修复：** 在严重和重要问题修复后，保留当前六个公开接口作为稳定门面，将纯合同解析、来源核验、GeNIS 归档和不覆盖发布/下载状态机拆为内部模块；不要在本轮以大重构替代最小正确性修复。

## 已确认满足的合同

- 六个公开接口名称、参数类型和返回类型与任务 01 计划一致。
- 真实生产 YAML 会被直接加载，加载器对顶层与主要子层未知字段、版本、阶段、状态、8 字段顺序、枚举、字段角色、Parquet、GeNIS、ns-3 和 A/B/C/D 预算执行精确比较。
- ZIP 核验实现会读取全部成员以触发 CRC 检查，并基于实际解压字节计算 10 秒成员哈希；文本路径穿越、重复成员、符号链接及常见 Windows 绝对路径已在实现中拒绝。
- 下载入口只接受登记的 Zenodo HTTPS URL；Range 仅在旁路锁完全匹配时发送，`206 Content-Range` 和 `200` 从零重启逻辑正确。
- 源锁不写运行时绝对根、时间戳或自引用，常规单进程路径使用规范 JSON 和稳定排序。

## 残余风险与待验收

- 本轮按简报禁止运行任何本机测试、格式化、服务器或网络命令，因此以上结论仅来自逐行静态审查。
- 修复后仍需在服务器项目根执行简报规定的 Black、Ruff 和 `tests/test_r2_protocol_contract.py` 全量目标测试。
- 正式 GeNIS、旧冻结输入和 TQH A/B/C 的服务器实物核验尚未执行；这属于环境验收缺口，不与上述实现缺陷混同。
