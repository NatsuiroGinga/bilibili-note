# 已发表方法池 BigBird 与 Longformer 的处置裁决

日期：2026-08-31
裁决人：主进程（用户授权「全权负责任务，不用等 codex」）
状态：**裁决为补跑，不收窄方法池**；执行阻塞于服务器不可达

## 一、被裁决的问题

`基线对比设计.md` 第 13 行规定「已发表方法池」固定成员为 7 个：XGBoost、GRU、全注意力、
BigBird、Longformer、随机森林、CNN。统一总表 `--probe` 实测只有 5 个有目标年读数：

| 成员 | 目标年实体 AP | 状态 |
| --- | --- | --- |
| XGBoost | `0.512899` | 已跑 |
| CNN | `0.409639` | 已跑 |
| 全注意力 | `0.353620` | 已跑 |
| 随机森林 | `0.260526` | 已跑 |
| GRU | `0.159956` | 已跑 |
| **BigBird** | 无 | **从未跑过** |
| **Longformer** | 无 | **从未跑过** |

二者既无运行目录也无任何结果。恢复卡此前登记的待裁决项是：补跑，还是在正文中把方法池
范围收窄并说明理由。

## 二、裁决：补跑

### 依据一：二者有同数据集已发表来源，且来源就是本池的主来源

裁决开始时我的假设是「BigBird 与 Longformer 可能在 LSPR 上没有已发表结果，因而本不该
入池，收窄是纠正而非妥协」。**该假设被原件核验推翻，如实记录。**

`wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md` 的全文笔记：

- 第 24 行 `baseline` 字段：「逐流 XGBoost、GRU、BERT 式全注意力、BigBird 和 Longformer；
  原始位置顺序为基础表示。」
- 第 76 行：「**Transformer**：BERT 式全注意力、BigBird 块稀疏注意力、Longformer 滑窗注意力；
  位置编码为无、正弦或 RoPE，按兼容性组合。」
- 第 23 行 `method` 字段：「统一比较八种流序列构造、XGBoost、GRU 和**三类 Transformer 编码器**」。

Dijk 2026 是本课题唯一的同数据集 XGBoost 配方来源，也是同数据集跨年评价的主参照。它评的
三类 Transformer 是一个整体，BigBird 与 Longformer 不是可选附加项。收窄方法池等于从唯一
同数据集来源里删掉它自己的两个基线，且删掉的恰是与本课题 FT 骨干最同类的两个长序列
Transformer——本课题的机制主张正是关于注意力骨干上的实体级低误报，缺这两行会让「FT 完整
方法在已发表方法中的绝对位置」这一问题失去最相关的对照。

### 依据二：两条轨道的冻结配置都已含二者

- `configs/lspr-baseline-matrix-track-a-q0-seed42-v1.json` 第 64–65 行，`model_order` 含
  `dijk2026_bigbird`、`dijk2026_longformer`。
- `configs/lspr-baseline-matrix-track-b-q0-seed42-v1.json` 第 68–69 行，同上。

二者是冻结配置里已登记的成员，不是新增。收窄需要改动已冻结的比较合同，而唯一理由是
「我们没跑」。

### 依据三：模型与训练入口都已实现，补跑不需要写模型代码

- `src/flow_probe/lspr_baseline_matrix_models.py` 第 15–16 行在 `NEURAL_MODELS` 中注册二者；
  第 147 行导入 HuggingFace `BigBirdConfig/BigBirdModel/LongformerConfig/LongformerModel`；
  第 152–166 行构造 BigBird（`block_size`、`num_random_blocks` 来自配置）；
  第 167–179 行构造 Longformer（`attention_window` 按层展开）。
- 第 44–45 行已有合同校验：Longformer 注意力窗口必须为正偶数。
- `src/flow_probe/lspr_baseline_matrix_train.py` 第 56 行 `MODELS = TABULAR_MODELS + NEURAL_MODELS`，
  第 748 行 `run_parser.add_argument("--model", choices=MODELS, required=True)`。

补跑的操作形态是同一入口换 `--model` 取值，与已跑通的 CNN、GRU、全注意力走同一条路径。

**成本估计更正（2026-09-01 实测）**：上文「成本是 GPU 时间，不是实现工时」**漏了一步**。
实际尝试启动 `dijk2026_bigbird` 时失败于
`FileNotFoundError: .../dijk-repro/cache/cache-manifest.json`——
矩阵训练器 `lspr_baseline_matrix_train.py` 读的是**另一套缓存格式**
（含 `cache-manifest.json`、`train_sequence.npy`、`normalizer_*.npy` 等），
而非四格所用的 `dijk-repro/cache` 目录。

服务器上现存的两份 `cache-manifest.json` 都不适用：
`runs/candidates/lspr24-rwkv-screen-seed42-v1/shared-cache/` 的
`train_sequence.npy` 形状为 `[100000, 5, 408]`（5 时间步、408 维），
与四格协议的 `(N, 128, 83)` 完全不同，属 RWKV 筛选的缓存；
另一份在 `runs/data-prepared/` 下，同样未核实为矩阵基线所用。

**第二次更正（同日，用户指出）：不得为此物化专用缓存。**

`llm_probe/AGENTS.md` 第 19 行明令：「统一清单与加载器服务传统模型、神经基线和候选，
**禁止模型专用重复物化**」。上一版更正写的「启动前须先做一次物化成本评估」方向错误——
问题不是物化贵不贵，而是**不允许物化**。

**由此暴露一个更实质的口径问题（待核，优先级高于补跑本身）**：
`lspr_baseline_matrix_train.load_cache` 硬性要求缓存清单的 `model_fields`
**恰有 `77` 个有序合法字段**（第 174–175 行），并要求 `final_accessed` 为 `false`；
而四格 FT 用的是 **`83` 字段**（本日 C00 v2 日志实测「数值 Token=81，词表 Token=2」）。

**即已跑的 5 个基线与四格处在不同的字段预算下。** 路线总控记载「字段预算为 Dijk 附录 A 的
83 字段」，且 `llm_probe/AGENTS.md` 说明「统一 83 字段只约束信息预算，不要求各模型用相同
张量布局、归一化或表示」——因此 `77 ⊂ 83` 时基线属**保守设定**（用更少信息），可接受但须说明；
若 `77` 含 `83` 之外的字段，则违反字段预算，那批基线结果不能进正文。

**该子集关系尚未核实。**

**处置（取代上一版的排期调整）**：

1. **先核实 `77` 与 `83` 的字段集合关系**，这决定既有 5 个基线的结果能否进「绝对位置」表——
   优先级高于补跑 BigBird／Longformer 本身。
2. 补跑只能走**统一加载器**：要么让矩阵训练器读四格所用的统一数据视图，
   要么确认既有的 77 字段缓存仍在且合法、直接复用。**两条路都不涉及新物化。**
3. 若两条路都不可行，则在正文如实说明该池只有 5 个成员有结果、
   BigBird 与 Longformer 因数据加载合同不兼容未能重跑，**不得为补跑而破例物化**。

### 依据四：收窄的代价不可接受

学位论文中把已冻结比较合同里的成员从「已发表方法绝对位置」表里删除，理由是未运行，属于
按结果可得性裁剪比较范围。这与 `AGENTS.md` 的「不得只报告挑选后的最好数字」同源：被删的
两个成员恰好是最同类的对照，删除方向对本方法有利，无法自证中立。

## 三、未决与阻塞

### 阻塞：服务器当前不可达（本机侧原因）

2026-08-31 本轮实测，SSH 两次失败，退出码 `255`，报文为 `Connection closed by 198.18.0.23`。
诊断结果：

- `dig +short connect.westd.seetacloud.com` 返回 `198.18.0.23`，属 `198.18.0.0/15`
  基准测试网段，是本机代理软件的 fake-IP。
- `nc -z` 报端口可达，但那是 fake-IP 代理伪造的 TCP 握手，不代表真实转发成功。
- `dig @223.5.5.5` 指定公共 DNS 仍未取到非 fake-IP 地址，说明 DNS 查询在本机被整体接管。

**结论：这是本机代理接管该域名导致的，不是服务器侧证据。** 需要用户在代理软件中为
`connect.westd.seetacloud.com` 添加直连规则，或临时关闭代理接管后重试。

**由此产生一个不能替代判断的事实：本轮无法确认 BER 水库分位数筛选臂是否仍在运行。**
它可能仍在训练，也可能已随服务器关机中断。恢复 SSH 后第一件事是只读核对该运行的状态、
最新日志行与检查点，再决定是继续等待还是从原子断点恢复；在拿到该证据前，不得对筛选臂
的结论或进度作任何陈述。

### 补跑前仍需核验的两项

1. **服务器 `transformers` 可用性**：`lspr_baseline_matrix_models.py` 第 147–149 行是
   可选导入，失败时抛 `BaselineModelError("BigBird/Longformer 需要正式环境中的 transformers")`。
   已跑通的 CNN/GRU/全注意力不经过该导入，因此「那三个跑通」不能推出 `transformers` 已装。

   **本机可查到的部分（2026-08-31 实测）**：`pyproject.toml` 第 15–24 行把 `transformers`
   放在 `gpu` extra 组，与 `torch`、`swanlab` **同组**；`uv.lock` 第 2276–2278 行锁定
   `transformers 4.57.6`。服务器既已运行 `torch 2.13.0+cu130` 且正式实验在用 SwanLab，
   该 extra 组**极可能已整组安装**。

   **但这是推论，不是实测。** 补跑前仍须在服务器执行一条导入确认：
   `uv run --no-sync python -c "import transformers; print(transformers.__version__)"`，
   期望 `4.57.6`。未装则 `uv sync --extra gpu`，装后记录实际版本。
2. **单模型耗时**：本轮未取到全注意力那次运行的实测耗时，`.Codex/docs/` 中检索到的
   「分钟级」是协议 B 的**评价续跑**（训练已完成），不是训练耗时，不可作为估算依据。
   恢复 SSH 后从已跑模型的运行目录时间跨度取实测值，再排队。**在拿到实测值前不写估算数字。**

3. **BigBird 的块稀疏注意力可能根本不生效**（2026-08-31 新发现，**补跑前必须实测**）。
   配置为 `block_size = 16`、`num_random_blocks = 2`、`attention_type = "block_sparse"`
   （`lspr_baseline_matrix_models.py` 第 33–34、162–164 行），而协议序列长度为 `128`。

   HuggingFace 官方文档（Context7 取自 `docs/source/en/model_doc/big_bird.md`）写明：
   「original full attention is recommended for sequences under 1024 tokens where sparse
   attention provides little benefit」，并要求「sequence length to be divisible by the
   block size」。后一条满足（`128 / 16 = 8`）；但前一条指出在 `128` 这个长度上，
   块稀疏相对全注意力**几乎没有收益**。

   HF 实现中还有一条自动回退：当序列长度不超过
   `(2 global + 3 sliding + num_random + buffer) × block_size` 时，会打印警告并把
   `attention_type` 切回 `original_full`。按本配置该阈值为 `9 × 16 = 144 > 128`，
   **预期会触发回退**。

   **此为推论，非实测**——本机 miniconda `rwkv` 环境无 `transformers`（实测
   `ModuleNotFoundError`），无法当下验证。补跑前须在服务器构造该配置跑一次前向，
   捕获 warning 并读取 `encoder.config.attention_type` 的实际值。

   **若确认回退**：BigBird 这一行实际跑的是全注意力，与 `dijk2026_full_attention_transformer`
   在机制上重合，正文**不得**把它写成「块稀疏注意力」基线，必须如实说明在本数据集的序列
   长度下该稀疏模式未激活。这不是取消补跑的理由——该行仍是 Dijk 2026 方法池的成员，
   且「在本任务的序列长度下稀疏注意力不适用」本身是可写入正文的有效观察。

   **Longformer 不受此影响**：`attention_window = 32`，`128 / 32 = 4`，滑窗注意力在该长度上
   正常工作。但同样须在补跑时记录实际生效的注意力模式。

### 执行清单（GPU 可达后）

按 track-A 与 track-B 各跑两个模型，共 4 次运行，沿用两条轨道各自的冻结配置，
不改 `epochs`、`batch_size_sequences` 或任何比较预算参数：

```
--config configs/lspr-baseline-matrix-track-{a,b}-q0-seed42-v1.json --model dijk2026_bigbird
--config configs/lspr-baseline-matrix-track-{a,b}-q0-seed42-v1.json --model dijk2026_longformer
```

优先级低于四格全即时重跑与 M-E 机制确立：本项是补齐已发表绝对位置表的缺口，不影响两个
机制的裁决路径，可在机制实验的 GPU 空档插入。

## 四、对恢复卡的写回

恢复卡中「已发表方法池缺两个成员」条目的待裁决状态改为已裁决：补跑，理由与依据见本文件。
在四次运行完成前，正文与统一总表不得按 5 个成员出「绝对位置」表。
