# DRIFT 逻辑路线隔离计划

## 目标

把 DRIFT 第三章从 RWKV 路线文档中逻辑分离，建立独立、可恢复、链接完整的 DRIFT 路线链；旧 RWKV 文档中的 DRIFT 内容只保留为迁移时历史快照。

## 边界与文件所有权

- 新建：`.Codex/docs/DRIFT/AGENTS.md`
- 新建：`.Codex/docs/DRIFT/DRIFT路线总控.md`
- 新建：`.Codex/docs/DRIFT/DRIFT第三章恢复卡.md`
- 新建：`.Codex/docs/DRIFT/DRIFT历史交接入口.md`
- 修改：根 `AGENTS.md`、`.Codex/docs/RWKV/RWKV路线总控.md`、`.Codex/docs/RWKV/RWKV第三章恢复卡.md`
- 检查并按实际结构最小处理：根 `CLAUDE.md`
- 更新：`.Codex/docs/PROJECT_INDEX.md` 及其可维护索引源；生成块只用既有生成器刷新
- 过程产出：本目录 `notes.md`、`迁移报告.md`、必要时 `Goal替换建议.md`
- 不触碰：实验代码、配置、数据、模型、日志、运行制品；不移动或删除历史文件；不执行 Git 分支或工作树隔离

## 阶段

- [x] 阶段一：重读全局、过程、RWKV 路线规则、总控、第三章恢复卡及朱论文分析
- [x] 阶段二：确定 DRIFT 原论文、结构化分析、DGA 综述、引用前沿综述的唯一规范入口
- [x] 阶段三：建立 DRIFT 独立规则、总控、精简恢复卡与历史入口
- [x] 阶段四：修改根路由、Claude Code 镜像入口和 RWKV 迁出声明
- [x] 阶段五：更新项目索引与可维护索引源
- [x] 阶段六：落盘可直接设置的新 Goal objective；目标工具因子线程不可见主 Goal 而未能替换
- [x] 阶段七：验证路径、关键词、规则链字节与差异格式，完成迁移报告

## 验收

- DRIFT 唯一恢复链先读原论文及结构化分析、DGA/引用前沿综述、朱论文分析，再读 DRIFT 第三章恢复卡。
- 恢复卡只保留数据合同、可复现实验事实、否决项、待证方向、唯一下一动作与证据链接。
- 根规则能按 `RESEARCH_ROUTE=DRIFT` 或明确 DRIFT 任务进入独立链；RWKV 不再吸收 DRIFT 当前状态。
- 所有新链接在同一工作树可达，`git diff --check` 通过。
- 迁移报告明确区分已完成的逻辑隔离与未执行的 Git 分支/工作树隔离。

## 当前状态

逻辑隔离全部完成并通过验证。唯一未完成项是主线程 `usageLimited` Goal 的工具级替换；完整 objective 已落盘，未创建错误的子线程 Goal。Git 分支与工作树隔离未执行，按两阶段合同留给主代理。
