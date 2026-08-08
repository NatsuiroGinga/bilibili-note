# R2 数据重建规划证据记录

## 只读来源

- `output/开题改进交接文档.md`：固定三源边界、共享预算、候选筛选顺序与论文主张边界。
- `output/第一创新点实验总控.md`：确认 R2 文献与合同已验收，但数据门禁为 `NO-GO`；A/C 与 B/D 的基线复用边界已经冻结。
- `.Codex/docs/research/protocol-adaptive-pinn/r2-data-rebuild-contract.md`：冻结字段、单位、四类视图、分组、泄漏审计、双构建和发布合同。
- `.Codex/docs/research/protocol-adaptive-pinn/final-report.md`：冻结 TCP/普通 UDP 专家、QUIC/未知回退、梯度隔离与 A/B/C/D 归因。
- `.Codex/docs/agents-split/remote-script-execution-contract.md`：冻结远程预检、白名单同步、持久化状态、`.partial`、原子发布和重启恢复要求。

## 已确认决策

- 分类共同输入必须保持既有 8 个公共数值字段及 8 个缺失掩码的名称、顺序与语义。
- GeNIS `TotBytes` 与网络层字节层级、`TcpRtt` 单位、`SrcWin`/`DstWin` 单位及缩放语义必须由一手证据闭合；没有证据时停止，不能猜测或填零。
- TQH-C2 必须由包序列重算聚合与序列哈希；包表不能假设同一 `sample_id` 在 Parquet 行组内连续。
- `profile`、地址、端口、服务、网址、密钥、明文、配置编号和攻击标签不得进入任何模型视图。
- ns-3 第一轮只生成配对的 TCP 与普通 UDP；共享守恒必须同时按包和网络层字节得到精确整数零残差。
- C 组是主方法；`C-A` 衡量物理路由贡献，`B-A` 只衡量协议直接信息，`D-B` 衡量相同额外信息预算下的路由增量。
- 数据构建与验证不使用 SwanLab；后续正式模型实验才使用固定在线项目。

## 2026-07-31 补充核验

### GeNIS 官方原件

- 官方登记为 Zenodo 记录 `14919237`，DOI 为 `10.5281/zenodo.14919237`，数据集版本为 `1.0.0`。
- `2-flows.zip` 官方下载地址固定为 `https://zenodo.org/api/records/14919237/files/2-flows.zip/content`，精确大小为 `380755720` 字节，官方 MD5 为 `063b7a2ec6e6b73cc302151d2b3ba6d7`。
- 服务器只读核验确认 `/root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip` 为 `380755720` 字节，既有下载日志记录来源为上述 Zenodo 文件且保存字节数为 `380755720/380755720`；`unzip -t` 已覆盖 5、10、30、60 秒四个尺度，每尺度 11 个攻击或良性 CSV，结尾为 `No errors detected`。
- 当前正式路径不需要重新下载。进入实现后仍须先匹配官方 MD5、计算 SHA-256，并把 ZIP 成员清单、各成员未压缩字节数与 SHA-256 写入源锁；本机 `raw/datasets/GeNIS-2025/2-flows.zip` 是不完整副本，禁止读取、修补或用于物化。
- 若服务器原件后续 MD5 或 ZIP 完整性失败，用户已授权只从上述官方登记来源恢复：使用同目录临时文件断点续传，严格校验网址、版本、精确大小、官方 MD5、计算后的 SHA-256、路径安全与关键成员清单后原子发布；不得以现有损坏副本续传或拼接。
- 官方记录还给出 `1-packets.zip` 的精确大小 `1028741083` 字节和 MD5 `5afbceaadfe3c3476f54723434d59b4a`。仅当 HERA 一手实现无法闭合 `TotBytes` 网络层语义时，才按同一官方来源流程取得包原件进行逐包复算；没有证据时不能把下载包原件本身当作语义已闭合。

### 现有实现风险

- `shared_b0_view.py` 已固定 8 个共同字段与缺失掩码，是字段顺序和现有换算的兼容基线；R2 应新建独立模块，不能原位改变旧 B0 物化器。
- GeNIS 当前候选标识由旧 `sample_id` 经 `sha256("dataset-candidate-genis-v0\\0" + old_sample_id)` 形成；必须枚举官方 CSV 原始行、重建旧标识后做一对一回接，禁止按标签或协议模糊连接。
- TQH 现有候选包聚合代码曾依赖同一 `sample_id` 的行连续性；R2 必须先按冻结样本集合过滤，再跨行组重组并按 `packet_index` 排序，测试必须包含交错样本和非相邻行组。
- `ns3_domain_randomization.py` 以同一奇偶索引同时生成 `traffic_mode` 与 `transport`，会形成协议与标签的确定性捷径；R2 不得复用该分配，必须先生成不含协议的基础配置，再为每个基础配置派生同种子的 TCP/普通 UDP 两条运行。
- `domain_randomized_queue_scenario.cc` 已有公开观测和队列守恒脚手架，但没有经核验的 TCP 内部状态 trace；第一轮预注册 `ns3::TcpNewReno`，至少 `CongestionWindow` 必须由 ns-3.48 实际 trace source 直接采集，其余候选状态只在服务器源码核验存在且定义稳定后进入模式。

### 确定性发布设计

- 两个构建器只写语义载荷、源锁、模式、审计和不含自指文件的载荷 Merkle 摘要，并保留 `_INCOMPLETE.json`。
- 验证器先比较两份语义载荷，再向两边写入逐字节相同的 `audits/deterministic-build-comparison.json`；随后写入绑定载荷摘要的 `freeze-manifest.json`，最后写入覆盖除自身以外全部最终文件的 `artifact-checksums.json`。
- 验证器移除两边临时标记后再次逐文件比较，仅把 build-a 通过同文件系统 `os.replace` 发布到固定根；build-b 留给人工复核，不自动删除。此顺序避免自指哈希环。

## 工作树边界

- 当前工作树存在其他任务的大量已修改和未跟踪文件，本任务不回滚、不暂存、不覆盖。
- 本规划任务唯一写入范围为 `.Codex/docs/sdd/task-r2-data-rebuild/task_plan.md` 与 `.Codex/docs/sdd/task-r2-data-rebuild/notes.md`。

## 阻塞事实

- GeNIS 服务器正式原始包的大小与 ZIP 完整性已闭合；仍须完成官方 MD5 匹配、SHA-256 与成员清单留痕、一对一回接，以及 `TotBytes`、`TcpRtt`、`SrcWin`、`DstWin` 的一手语义门禁。
- TQH 协议与标签共同支持、匹配子集、留采集配置、去握手和字段置换审计尚无制品。
- 新 ns-3 配对制品与 TCP 内部状态真值尚未生成和验收。
- R2 统一编排器、验证器、配置和双构建发布制品尚未实现。

## 规划过程中的失败与处置

- 首次创建 `.Codex/docs/sdd/task-r2-data-rebuild/` 因目录写权限被拒绝；经受控权限批准后只创建本任务目录，未修改其他路径。
- 两次本地模式探查脚本未成功取得目标信息；未据此推断字段或单位，后续结论均来自已读取源码、合同、官方元数据或服务器只读核验。
- 本机 `2-flows.zip` 缺少 ZIP 中央目录；该文件被明确排除，不执行修复、续传、拼接或物化。
