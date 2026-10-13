# 任务计划：第三章可借鉴方法挖掘（2026-10-13）

> 任务简报来源：主代理派发。工作树 `/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`。
> 交付物：`thesis/methods/第三章-可借鉴方法清单.md`。
> 性质：方法挖掘（找可拿来用的技术），不是文献核查（不问谁做过）。

## 五个难点（交付按此分节）

1. 离散空间「反应项」的梯度估计/可微化技术（straight-through、Gumbel、REINFORCE、黑箱求解器差分、隐式微分、切平面、其他）
2. 预算/难度自适应调度（DES、SAAT 之外；模型状态驱动的调度）
3. 离散对抗样本生成器（组合优化、贪心、束搜索、语言模型引导；替代随机替换）
4. 极低误报（0.1%/1% FPR）下的训练与阈值标定
5. 训练威胁集与评价威胁集不匹配（Tramèr & Boneh 2019 之后的覆盖更宽威胁集方法）

## 检索入口顺序

1. 本地：`uv run --project scripts/literature_search --locked python -m scripts.literature_search query "..." --scope local --mode hybrid --json`（后台跑；索引 stale 则按既有核查记录降级 rg）
2. 直接读 `wiki/papers/methodology/adversarial-training/`、`wiki/papers/attack-detection/dga/`、`wiki/papers/methodology/`
3. 新 PDF：`raw/papers/attack-detection/`（BiGrad、SAAT、BETA、悲观双层——先逐个识别文件名）
4. Zotero MCP 语义检索 + 全文
5. WebSearch（WebFetch 本机被阻断，需下 PDF 报主代理）

## 进度检查点（收尾状态，2026-10-13）

- [x] 读完既有 `thesis/methods/第三章-离散反应项文献核查.md`（已知：BiGrad 式(6)-(9)、Jurečková 式(2)(3)、Drichel 随机预算、DES/SAAT 在线摘要级）
- [x] 五个新 PDF 原件逐个核对：BiGrad p.3–4 式号复核、BETA p.4–7、SAAT p.1–7、悲观双层 p.1–14、RS-Del p.1–5
- [x] 难点 1：四族机制收敛（STE／Gumbel/Concrete／解映射平滑［Berthet Def 2.1 p.3、DBB 式(7)(8)、I-MLE］／分布参数化［Benfield 式(5)(6) p.9 + 式(7)(8) p.12］）
- [x] 难点 2：SAAT 式(5) p.5+算法1 p.6；IAAT 式(2) p.3+算法2 p.3–4（本地笔记已核）；GAIRAT 式(5) p.5；FAT 式(3) p.3；A³ 式(14)(15) p.5；Wasserstein 漂移判据；DES 题录核验但全文 unavailable
- [x] 难点 3：HotFlip 式(1) p.2（/tmp 原件核）+ Drichel DGA 先例；DeepWordBug/GA-PSO/LM 引导逐条裁定
- [x] 难点 4：Tong 2018 次序统计量（本地笔记）；LibAUC pAUC 式(2)(3) p.3；top-K 校准铰链式(1)–(5) p.2–3；RS-Del 阈值 η；PU/异常检测/代价敏感排除理由
- [x] 难点 5：Tramèr Max/Avg p.6、表1 p.8；BETA 逐错类分解 p.5；RS-Del Table 1 p.5；Drichel LOGO p.10；Kang/Jia/Maini 题录级
- [x] ID 证伪记录：WebSearch 给的 Berthet=2006.16219、Maini=2010.15268 等 ID 经 arXiv API 证伪；所有采用 ID 经 API 复核
- [x] 写交付 `thesis/methods/第三章-可借鉴方法清单.md`（五个难点各节 + 推荐组合 + 覆盖面声明 + 补下载清单）

## 遗留缺口

- DES 全文在 arXiv 当前返回 unavailable，需主代理择机重下（本地 PDF 为 HTML 页）。
- Maini「L0-Robustness via L∞-constrained AT」ID 未核验（WebSearch 三个候选全证伪），仅题录候选。
- Gao 2019 DeepWordBug 分类版（arXiv:1901.10633）、Zhu 2022（pAUC 原文）、Tong 2018（JMLR 版）未取 PDF 原件；
  Tong 2018 依赖本地 MinerU 全文+笔记，正式引用前建议补 JMLR 原件。
- /tmp 下已核副本（`/tmp/hotflip_1712.pdf`、`/tmp/cand_*.pdf`）可直接移入 raw/papers/ 入库，避免二次下载。

## 纪律

- 不列「相关但用不上」的文献；每条答「能不能用在我们场景」（固定长度、字符级替换、只改可编辑位、点号冻结、二分类、低误报）
- 引用回原件核页码/式号；未取全文的标证据等级
- 不 commit、不改交付物以外的受管文件；零训练、CPU 可读制品
