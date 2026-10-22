# LAMDA 成文阶段恢复卡（第四、五章与全章成文）

> **更新**：2026-10-22 深夜（本机弃用、切换新设备前的完整交接）。
> **前序**：`checkpoint-8-第四章进度.md`（§一–§十六，实验矩阵全记录）。
> **本机**：Mac（MPS）；**新机**：克隆仓库后按本卡从「立即待办」开始。

---

## 一、当前进度（一句话）

第三章已定稿（0.8170）；第四章实验矩阵**闭合**（整合方法 +1.54 pp，CI [1.22, 1.87] 排除零；
机制二三轮探索按硬止损关闭，负结果转"成员分工的作用面分析"）；第二章草稿成稿并过自审
（六项全过、阻断 0）；第五章内核三格收据入库、Go/Gin 后端阶段 A 入库；**第四、五章正文未起笔**。

## 二、立即待办（新机克隆验证后按序执行）

0. **新机起点（必读）**：`git clone` 默认落在 `main`（旧路线）——**必须先 `git checkout exp/ch3-lamda-20260908`**，一切工作在该分支根目录进行（无需重建 `.worktrees/` 结构，那是旧机的布局）；本工作树的根 `CLAUDE.md`/`AGENTS.md` 路由链已指向本卡。然后按 1.8170 复现门验证环境。
1. **克隆验证门槛**：`tools/ch3_lamda_domain_il_e4.py` 复现门（12y = 0.8170，MPS/CUDA 序列各自成立）；
2. **full 格重跑**：`tools/ch5_system_runner.py` 的 full 格（三格 result 已在
   `runs/diagnostics/ch5-system/`，full 于本机死亡于 2018 epoch 8，约 14 分钟）；
3. **HF 托管已生效（勿重复上传）**：第五章评测基准的大文件已托管至 HF 数据集仓库 `Heehobino/lamda-ch5-eval-benchmark`（panel_2024.f32 168 MB、tabm4_state.safetensors、panel_2024_meta.json；版本化提交哈希 3801db96/63993fa2/4aaf99df 见 `runs/diagnostics/ch5-eval-benchmark/data/README.md`）。新机恢复：`hf auth login`（账号 Heehobino）后 `hf download Heehobino/lamda-ch5-eval-benchmark --repo-type dataset --local-dir <同目录>/data/`；
4. **Rust 检索续做**：`.Codex/docs/2026-10-22-rust-python服务对比检索/`（已有 TechEmpower r23 数据表；
   三问检索＋裁决输入表待续；rust-skills 需在新机 `~/.claude/skills/` 重装）；
5. **第四章正文**：按重构骨架 4.1（问题=第三章边界）→ 4.2（形式化）→ 4.3（方法）→ 4.4（算法 4-1）→
   4.5（理论：双通道账＋精确 F1 分解＋合流曲线＋梯度性质）→ 4.6（实验矩阵）→ 4.7（小结导向第五章）；
   素材：`第四章-整合方法重构决定.md`、`第四章-去相关惩罚的梯度性质.md`、`第二三四五章衔接设计.md`、
   各 result JSON＋bootstrap；
6. **第五章正文＋平台阶段 B/C**：Web 前端（Vue3）、集成测试、功能用例表（栈与模块见
   `第五章形态与实现计划.md`，Go/Gin＋GORM/MySQL，DSN 走 `CH5_MYSQL_DSN`）；
7. **图件**：双通道分解图、S1' 合流曲线、k 曲线、参数-性能对照（数据全在库）；
8. 每章 paper-self-review 门禁。

## 三、关键文件地图

| 类别 | 路径 |
|---|---|
| 检查点（实验全记录） | `.Codex/docs/2026-10-20-上下文压缩恢复/checkpoint-8-第四章进度.md` |
| 章际衔接设计 | `thesis/methods/第二三四五章衔接设计（照参照论文）.md` |
| 第四章重构决定 | `thesis/methods/第四章-整合方法重构决定.md` |
| 理论件 | `第四章-单次预算下的年度风险最小化形式化.md`、`第四章-TabM集成机制理论推导.md`、`第四章-去相关惩罚的梯度性质.md`、`第四章-评测平均刻画与成员年度锚定形式化.md` |
| 三轮先导设计 | `第四章-成员年度锚定先导设计.md`、`第四章-NCL与训练通道诊断先导设计.md`、`第四章-成对相关惩罚先导设计.md` |
| 基线与系统设计 | `第四章-外部基线矩阵设计.md`、`第五章形态与实现计划.md`（含 Docker 化与 GPU 迁移清单） |
| 第二章成稿 | `thesis/chapters/第二章-LAMDA/`（7 文件）＋自审 `.Codex/docs/2026-10-22-第二章自审/` |
| 平台后端 | `platform/backend/`（Go/Gin＋GORM/MySQL，DSN 走 `CH5_MYSQL_DSN`） |
| 实验制品根 | `thesis/experiments/llm_probe/runs/diagnostics/`（ch4-lamda-* 各目录） |

## 四、不可让渡的纪律（新机同样生效）

1. 训练单种子 42；配对 bootstrap 量化不确定性，不重训；
2. MPS 序列已归档制品为冻结证据；换 GPU 后 CUDA 序列全矩阵重跑、不与 MPS 读数混写；
3. 正文禁负面落差框架（数据全呈、归因中性）；三轮负结果写"成员分工的作用面分析"；
4. 凭据只走环境变量（`CH5_MYSQL_DSN`）；Zotero API key 轮换仍未做（历史 6 提交泄露在案）；
5. 每章定稿前 paper-self-review 门禁。
