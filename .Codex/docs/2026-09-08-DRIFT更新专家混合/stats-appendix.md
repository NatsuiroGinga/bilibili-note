# DRIFT 更新专家混合统计附录

<!-- RESEARCH_ROUTE=DRIFT -->

## 一、有效统计

- 运行数：`1`。
- 折数：`1`，仅折0。
- 种子数：`1`。
- 训练块：`1` 个固定块，32768样本、32个连续批次。
- 比较：三个臂从相同端点、优化器状态和固定块出发。
- 有效报告：各臂精确聚合指标、配对差值、预注册布尔门、运行与裁剪收据。

## 二、无效统计与原因

| 统计量 | 状态 | 原因 |
| --- | --- | --- |
| `mean ± std` | 禁止 | 没有独立重复运行 |
| 95%置信区间 | 禁止 | 无法估计跨折、跨种子或跨块方差 |
| 参数或非参数显著性检验 | 禁止 | 有效独立样本数为1 |
| 标准化效应量 | 禁止 | 缺少独立重复的方差估计 |
| 多重比较校正 | 不适用 | 未执行推断检验 |
| 把32批当 `n=32` | 禁止 | 批次属于同一依赖优化轨迹 |
| 把225180预测行当独立重复 | 禁止 | 行共享同一模型、端点和训练轨迹 |

## 三、指标方向与主门

- 良性 BCE、DGA micro BCE、DGA family-macro BCE、FPR、FNR：越低越好。
- AP、AUROC：越高越好。
- 预注册主门只使用三项 BCE：混合臂相对 `no_update` 三项均非增，且至少一个 DGA BCE 严格下降；另须相对 `joint_all_equal` 三项均非增且至少一项严格下降。
- 实测 `passes_no_update=false`、`passes_joint_all_equal=true`，因此总体否决。

## 四、完整性与哈希

| 制品 | SHA-256 |
| --- | --- |
| `result.json` | `d7efad0d5e740bcf58604ed7d0698617dae5c9cfd71fb91910c354a71321e328` |
| `status.json` | `51c1857dd36f8c157d9f11888db48ca16fe25a96cc4e7b25aeb0aa46c5a0c67b` |
| `checkpoint.pt` | `f81056a5003df256e12d04429257bc13af884a5942711f4bff5445873ab5efa6` |
| `manifest.json` | `89e4cbe2bbb37f841b9f6a0f209da318a90c5a8fbf1f7b24e9b89ffc0b0b66fe` |

`status=completed`、`stage=completed`，清单列出三个 arm、求解收据、结果、检查点与运行日志。`forbidden_years_accessed=[]`。

## 五、统计结论

本附录不提供统计显著性结论。唯一合法裁决是：在该确定性筛查实例上，固定混合违反预注册的良性 BCE 非增门；结论不外推到其他折、种子、训练阶段、目标年份或其他门控形式。
