# 任务2：正式固定成员与流式数据审计

> **已取消（2026-09-13 14:37）**：用户重申不允许物化，主代理已立即中断本任务实现代理。下文仅留失效派工记录，不可执行；正式接口改走现有数据直读，不新建派生数据或物化工具。

## 目标与独占文件

落实 `implementation_plan.md` 任务2和§3.2，让两骨干及全部训练臂消费共同源数据、目标成员和审计清单。你不是唯一代理，不覆盖/回滚/暂存其他改动，不建子代理或新DRIFT分支，不做Git写操作。

新建以下文件，路径相对 `thesis/experiments/llm_probe/`：

- `tools/ch3_drift_formal_members.py`：Python组织、合同调用及阶段清单。
- `tools/ch3_drift_materializer/Cargo.toml`、`Cargo.lock`、`src/main.rs`，必要时同目录 `src/lib.rs`：Rust流式Parquet、SHA-256、磁盘去重及确定性采样。
- `scripts/remote_launchers/run_ch3_drift_formal_assets_v1.sh`：复用现有正式远端入口的薄启动器。

允许最小修改 `tools/ch3_drift_formal_contract.py` 接入已实现成员阶段，不更改冻结值、安全或状态语义。不改三配置、旧脚本、通用启动器、Python依赖锁或恢复卡。报告和技能收据分别放本目录 `task-2-report.md`、`task-2-skill-receipt.json`。

## 固定接口与科学边界

- 先读本简报，再读计划§1、§3.1/3.2及任务2；公共函数以现有合同模块及task-1-report.md为准。
- `load_config`返回配置与规范哈希；相对路径由明确根解析，不能把已解析绝对Path重新交给只收相对路径的API。
- revision和30角色来自评价配置；文件、角色、标签一一对应，禁止清洗exact eSLD或按模型输出筛选。
- 源训练为T17–T19 train+test合并后unique；源验证为三年val合并后unique。保存代表来源和来源集合，不继承旧重复曝光。
- 年度目标每类按exact eSLD去重、完整SHA-256升序取`min(200000,unique_count)`，无member_seed；源阈值良性清单用全部唯一成员，不套200000上限。
- 源训练/验证交集先审计，不能自行删样本或重新划分。未决校准资格单独标记；新实体政策未冻结，只产资格审计，不标正式新实体面板。
- 生成计划规定的input/member/dedup/label-conflict/cross-role-overlap/member-count清单、源训练/验证磁盘表与共同源良性、年度目标成员。T25带_test文件不得混入目标角色。

## 工程实现

1. Python仅组织；按运行合同，大规模扫描/哈希/去重热路径用Rust。不用Python逐行UDF处理全量，不构造全量字符串列表或无界HashSet。
2. 有界批次与磁盘分区、外排或磁盘数据库完成去重和交集；报告每类内存状态上界、最大打开文件数、中间磁盘和总I/O。读取批次作为工程参数，不能改变成员。
3. 每角色/分区完成后保存可恢复进度。输入、配置、代码身份一致才复用；保留partial，完成后原子发布最终路径和哈希。
4. 长阶段记录开始、结束、跳过、失败和限频心跳，报告实际行数/吞吐，不打印原始域名或凭据。
5. 新Rust工具独立于旧研究代码；可参考既有Cargo依赖版本，首次API不确定按Context7或官方文档核验。Cargo.lock由Cargo生成；不新建Python环境，不改全局工具链。
6. CLI支持审计、物化、恢复，以及源资产独立完成。部分完成需列缺项，不能伪造全资产complete。真实T17工程核查可以限定明确源验证角色，但必须标engineering_only且不改变正式全量模式。

## 运行与验证

- required_skills：`/Users/bilibili/.codex/skills/backup/daily-coding-20260811-112930/SKILL.md`、`/Users/bilibili/.codex/skills/backup/rust-skills-20260811-112930/SKILL.md`。按 `.Codex/docs/agents-split/coding-agent-skill-receipt.template.json` 完整登记字段、真实读取时刻与哈希，实际产物均须在所有权表中。
- 读取实验、脚本AGENTS和匹配的按需运行合同；不导入或分配MPS/CUDA，MP正在本机训练。
- 不运行black、cargo fmt、Prettier、人工夹具、单元/集成测试。执行相关语法/Cargo构建/CLI/Shell检查，随后用真实T17完整验证文件做工程审计与物化，核对计数、唯一成员、标签、来源和哈希，制品放受管runs目录。
- 本机不得执行超过运行合同规模的全T20或全30文件内容物化。服务器执行全量及T20不同批次复算；先交代码、小规模真实制品与精确服务器命令，不因服务器身份待核而跳过实现。
- 编译控制资源并记录实测，不能默认全核挤占MP。可离线复用已有依赖，下载走正常授权。
- 未完成服务器全量审计时标“实现与T17工程核验完成，全量验收待执行”，不得缩小完成条件。

## 交付

报告精确文件、公共CLI/函数、依赖/API来源、命令/返回码、真实T17制品与资源实测、源/目标阶段状态、全量未决项。主代理独立验收后进入任务3；本报告不裁决F或MP效果。
