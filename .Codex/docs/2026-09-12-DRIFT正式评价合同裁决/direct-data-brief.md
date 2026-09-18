# 正式评价：现有Parquet直读与确定性成员接口

## 目标与所有权

这是已批准正式评价计划的下一项实现，不改变数据角色、训练臂、指标或数值。读取本简报、修订实施计划§3.1–3.2和任务1、现有合同模块及三配置，再改代码。按用户裁决使用 `gpt-5.6-luna`，父代理选 `high`：跨配置、角色、去重和下游身份耦合较多，但不含新科研设计。

独占以下五个生产文件：

- `thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py`
- `thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py`（新建）
- `thesis/experiments/llm_probe/configs/ch3-drift-formal-evaluation-v1.json`
- `thesis/experiments/llm_probe/configs/ch3-drift-official-p2p3-formal-v3.json`
- `thesis/experiments/llm_probe/configs/ch3-drift-bresnet-p2p3-formal-v1.json`

过程报告和技能收据为本目录 `direct-data-report.md`、`direct-data-skill-receipt.json`。允许正常小型JSON审计收据，不写成员、源训练/验证副本、攻击数据、数据库、磁盘索引、缓存分区或Rust项目。不修改编辑模块、两骨干训练脚本、远程启动器和恢复卡。你不是唯一执行者，不覆盖/回滚他人改动，不暂存或提交，不派下级代理。远程启动器另行接续，本任务不连接服务器、不训练、不调用MPS/CUDA。

## 共享合同最小改动

1. 保留已验收路径安全、30角色绑定、长度前缀、哈希、状态机、训练数值和攻击/阈值。不得重写框架。
2. 所有配置移除 `materialize` 可用模式；合同门名称 `assets` 改为 `inputs`，旧入口拒绝并中文说明，不创建假通过状态。
3. 评价配置新增严格的 `input_access`：模式 `direct_parquet_read_only`，源顺序 `input_role_order_then_row_first_occurrence`，去重键 `exact_esld`，派生数据写入 `false`。训练配置的 `input_views` 改为直接引用共享评价角色：训练 `source_train_test_exact_unique_in_memory`、验证 `source_val_exact_unique_in_memory`。仅这些接口字段发生变化，原数值、30路径、批准面板和身份命名空间不变。
4. 输出角色必须区分数据副本与合法预测/模型/统计；本任务的数据工具只写聚合JSON，不以 `.parquet` 后缀全面禁止未来预测制品。不要实现尚不存在的训练/评价门为通过。
5. 公共 `load_config` 等签名保持；编辑模块通过旧公共接口正常加载修订配置，编辑随机算法及三档输出不得改变。配置哈希变化要明确登记，旧审计收据原样保留。

## 直读接口与算法

按照实施计划实现 `audit_inputs`、`load_source_unique_in_memory`、`iter_target_selected`、`count_target_unique_in_memory`；完整函数签名、返回模式和消费示例写入报告，后续两骨干与评价器共用。模式为 `ch3_drift_direct_data_v1`，禁止把生成器结束前的部分处理标成完成。

- 用现有PyArrow批读取原 `domain,label`，不清洗域名。标签严格与角色的benign=0/dga=1一致，空/非字符串/空域名/非法标签失败。记录元数据行数、实读行数、SHA-256、范围、状态；只扫描实际请求角色，不能谎称其他角色已全量核查。30文件存在性/元数据与全内容审计是不同状态。
- 源Store只驻内存，按配置角色顺序及行序保留首次出现的exact域名；同域名同标签去重，不同标签必须报告冲突且不能静默选择。返回稳定的域名与标签访问接口、原始/唯一数及顺序根摘要，禁止序列化Store。全源训练组为12个train/test角色，验证组为6个val角色；共同良性阈值组为3个benign val角色。不重新划分或过滤训练—验证重合。
- 目标单元完整扫描一次，最大堆保存最小200000个完整SHA256成员键；堆内exact域名去重，排序以完整成员摘要，出现摘要对应不同域名时保留错误计数并失败。已被淘汰的大键无需永久保存，后续同键重复不会重新超过单调下降的入选上界。最终按成员摘要排序并流式返回批次，在迭代前或完成时暴露选择收据。成员哈希复用合同的namespace/revision/panel/year/class/exact_esld编码，不设置额外种子。
- 前200000选择器不能给全体 `N_unique`：超过上限时明确未知，而不是把堆大小或原始行数当唯一数。整集合精确计数为单独操作，仅在明确容量允许时用内存集合做；未执行只阻断release_weighted等依赖统计，固定成员选择与纯DGA指标不受阻。
- 源训练—验证重合、目标新实体、family资格仅输出实际范围计数和待裁决状态；不得擅自删除实体、创建家族分面或改变主面板。
- 所有输入只读，集合/索引只存在进程内；出现容量不足明确停止受影响操作，绝不自动落盘。批读取、堆、集合和输出数组内存同时计算，不能把源唯一化冒充O(200000)。全源/完整目标大操作的服务器容量收据后续独立完成，本机本任务禁止执行。

## 本轮真实验证

本机解释器固定 `/opt/miniconda3/envs/rwkv/bin/python`。PyArrow接口先依据实际25.0.1版本核验官方文档/Context7并留来源；不改依赖。模块顶层不导入torch，PyArrow延迟到读取入口。

提供 `--config --run-dir --audit --scope development`：只读取完整 `T17_benign_val` 和 `T17_dga_val` 两文件（各150000行；运行时核对元数据，不靠此文字硬造结果），用源Store、标签冲突和固定哈希选择共享内核完成真实审计。不读目标年份、不缩小正式目标上限。若用源面板验证选择内核，使用明确 `engineering_only` 身份，不能伪写T20或宣称完整目标堆淘汰路径已覆盖；实际输入未覆盖的分支留待服务器真实单元验证，不创建夹具。

运行目录为 `runs/diagnostics/ch3-drift-formal-direct-read-development-v1`；已有目录则先读状态，保留旧收据并使用明确后缀的新身份，不覆盖首次结果。只写小JSON：输入身份、实读/唯一/冲突数、所选根、容量实测、算法版本、范围和未验证项。禁止原域名、逐实体清单或攻击字符串。校验选择成员根不依赖读批大小；同一真实输入可用第二批大小在新目录复算，不把两次工程核查当两次实验。

语法/入口检查后立即真实运行，不创建人工单元/集成/冒烟夹具，不跑格式化器。无效输入和命令参数可用CLI检查，不造数据。修订配置后只验证已实现模块依赖兼容，不能运行尚不存在的后续训练。

## 技能与检查点

`required_skills`：`/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`，改码前完整读并登记SHA256和时间，按完整既有收据模式填写所有权、命令/退出码、真实运行 `real_run.evidence`。预计超过30分钟时每完成一个接口即写报告检查点；不能把未完成内容一直留在对话。收据验证器由主代理只执行一次。

交付须区分：已实现接口、真实T17覆盖、未运行的全源/目标/服务器容量验证。保留所有旧制品，不把已取消物化任务改写为完成。
