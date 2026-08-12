# 复杂度与资源约束规则更新报告

## 使用流程

已读取并采用 `/Users/bilibili/.codex/skills/skill-improver/SKILL.md` 的计划、分组、备份、更新与核验流程。

## 修改状态

- 已修改：`thesis/experiments/llm_probe/AGENTS.md`，加入百万级物化状态上界硬门禁。
- 未直接修改：两份仓库外技能及其规则目录。
- 已生成：`rust-skills-complexity-resource.patch`，包含日常编码检查项、两条 Rust 规则、规则计数和快速引用更新。

## 计数变化（补丁应用后）

- `rust-skills`：265 条规则增至 267 条规则。
- 类别数：保持 26 类。
- 性能模式类别：13 条增至 15 条。
- 技能版本：`1.5.1` 增至 `1.5.2`。

## 备份与核验

- 备份：未完成。`backup-skill.sh` 创建 `/Users/bilibili/.codex/skills/backup/` 时被权限拒绝。
- Context7 核验：使用 Rust 标准库 `/websites/doc_rust-lang_stable_std`。已核验 `BufReader`/`BufWriter` 通过内存缓冲减少小而频繁 I/O 的系统调用，`BufWriter::flush` 用于把缓冲数据写入底层写入器，`HashMap::capacity` 仅为无需再分配的容量而非元素上限，`BTreeMap::entry` 可随新键增长；因此两条 Rust 规则要求在新键插入或入队前检查逻辑上限，并将缓冲容量计入峰值内存和 I/O 预算。
- Context7 核验：使用 Tokio `/websites/rs_tokio_1_49_0`。已核验有界 `mpsc::channel(capacity)` 的容量至少为 1，队列满时 `send` 等待接收方从而提供背压，`reserve` 可等待容量；因此补丁禁止以无界队列掩盖积压，并要求固定队列容量与超限处理。
- Context7 局限性：标准库和 Tokio 文档提供集合、缓冲、文件与有界队列 API，不规定具体业务分区、驱逐或磁盘溢写阈值；这些阈值必须由输入规模、每键状态字节数、磁盘余量和吞吐预算计算后写入运行合同。
- 最小核验：已检查补丁中的目标路径、规则标识符、计数替换和内部链接；`daily-coding` 与 Rust 版本、总数、类别计数差异块已通过无写入 `patch --dry-run` 匹配。Rust 的性能快速引用和任务映射差异块在当前 `patch` 实现中未匹配，尚不能宣称整个补丁已完全通过可应用性核验；未运行格式化、测试或 `verify-update.sh`，符合本任务限制。
