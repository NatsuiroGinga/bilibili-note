# 第三章候选框架：LAMDA 恶意漏判修复与 PCT 联合维护

**状态：外部方法来源＋LAMDA 任务化候选，尚未在 LAMDA 上验证。**

## 1. 框架目标

LAMDA 的年度模型更新同时面对三种不同变化：

1. 当前年度已确认的恶意样本可能被上一冻结模型漏判，需要恶意正向修复；
2. 更新模型可能把上一模型已经正确判别的样本改错，需要抑制旧正确决策回归；
3. 修复恶意漏判容易把良性样本推过告警阈值，需要独立控制真实 FPR。

因此，联合框架不是“Replay 再加一个通用蒸馏项”，而是将三个职责显式分离：

- 修复项只看旧模型漏判的当前真实恶意样本；
- PCT 项只保护旧模型正确决策；
- FPR gate 只负责检查点资格和部署验收。

## 2. 因果信息集合

年度 (t) 更新开始时允许使用上一冻结模型 (f_{\theta^-})、当前已到达的训练标签 (D_t^{train})、历史回放 (B_{t-1})、固定阈值 (a) 和已冻结统计。测试标签、封印年标签、未来家族统计和未确认伪标签均禁止使用。

## 3. 机制一：恶意漏判定向修复

旧模型 logit 为 (z_{\theta^-}(x))，当前训练区中旧模型漏判的真实恶意集合为：

\[
R_t=\{(x,1)\in D_t^{train}:z_{\theta^-}(x)<a\}.
\]

对每个样本定义 margin 缺口：

\[
d_i=[a-z_{\theta^-}(x_i)]_+.
\]

修复损失为：

\[
L_{mal\text{-}FN}(\theta)=
\frac{\sum_{i\in R_t}d_i\,\operatorname{BCE}(f_\theta(x_i),1)}
{\sum_{i\in R_t}d_i}.
\]

它只利用当前已到达的真实恶意标签，目标是提高恶意正向修复率，不对所有恶意样本无差别加压。

## 4. 机制二：PCT／Focal Distillation 旧正确决策保护

令 (C_t) 为当前训练区与历史回放中上一冻结模型正确判别的样本：

\[
C_t=\{(x,y)\in D_t^{train}\cup B_{t-1}:\hat y_{\theta^-}(x)=y\}.
\]

PCT 的 Focal Distillation 形式可写为：

\[
L_{FD}(\theta;\theta^-)=
\frac{1}{|S_t|}\sum_{i\in S_t}
\left(\alpha+\beta\mathbf 1[i\in C_t]\right)
D\!\left(q_{\theta}(x_i),q_{\theta^-}(x_i)\right),
\]

其中 (S_t) 是允许使用标签的当前／历史样本集合，(D) 可取 PCT 的 logit matching 或温度缩放 KL；旧正确样本获得额外权重。PCT 原方法是安全回归直接基线，本框架不把它改名为新机制。

## 5. 联合训练目标

基础回放目标为 (L_{base}=L_{cur}+L_{replay})。联合模型在每个年度更新中优化：

\[
L_{joint}(\theta)=L_{base}(\theta)
+\lambda_rL_{mal\text{-}FN}(\theta)
+\lambda_pL_{FD}(\theta;\theta^-).
\]

PCT 的 alpha、beta、温度以及两个损失权重必须在源年／项目开发层预注册，不能用封印年结果回调。

## 6. 独立 FPR gate

训练代理不等于真实 FPR 保证。每个检查点 (k) 在独立且时间一致的良性 gate 集合 (G_t^0) 上计算：

\[
\operatorname{FPR}_{gate}(\theta_k)=
\frac{\operatorname{FP}_{gate}(\theta_k)}
{\operatorname{FP}_{gate}(\theta_k)+\operatorname{TN}_{gate}(\theta_k)}.
\]

只有满足

\[
\operatorname{FPR}_{gate}(\theta_k)
\le \operatorname{FPR}_{gate}(\theta^-)
\]

的检查点才有资格按 FNR、恶意正向修复率和 AP 排序。该 gate 是模型选择与部署验收条件，不是对未知未来年份的数学保证。

## 7. 与“博弈候选”的关系

本框架的第一版可只使用硬 gate，不引入双玩家乘子。若简单 gate 无法在保持 FPR 的同时获得恶意修复，再把 gate 升级为 Cotter／TFCO 风格的约束玩家：模型玩家优化 (L_{joint})，安全玩家更新 FPR／回归约束的拉格朗日乘子。这样可避免在简单方案尚未验证前直接引入高复杂度博弈。

## 8. 最小实验矩阵

只使用来源年 `2013/2014` 和项目开发层 `2016/2017`：

| 实验臂 | 恶意漏判修复 | PCT／FD | FPR gate |
| --- | ---: | ---: | ---: |
| ER | 否 | 否 | 同一验收规则 |
| ER＋PCT | 否 | 是 | 同一验收规则 |
| ER＋恶意漏判修复 | 是 | 否 | 同一验收规则 |
| ER＋恶意漏判修复＋PCT | 是 | 是 | 同一验收规则 |

已有缺口修复单臂可作为先导证据，但正式联合比较应固定同一初始化、容量、年度顺序、训练预算和 gate。阈值匹配应作为额外控制，排除“只是改变 operating point”的解释。

## 9. 通过与失败门

相对 ER，候选必须同时满足：

1. `FPR_gate` 不增加；
2. FNR 严格下降；
3. 旧恶意负向翻转率不增加；
4. 恶意正向修复率有改善；
5. 联合臂不劣于两个单臂。

只降低 NFR 而提高 FNR，或只降低 FNR 而显著提高 FPR，均不能进入封印年。若 PCT 保护过强导致恶意修复消失，应保留为直接基线而不是主算法。

## 10. 创新边界

PCT、Focal Distillation、Replay 和 FPR 约束均来自成熟方法家族。潜在创新主张只能是：针对 LAMDA 时间漂移，把恶意漏判修复与旧正确决策保护按不同错误面耦合，并以时间一致的 FPR gate 统一模型选择。该主张必须由 LAMDA 源年和封印年制品支持，不能由外部论文结果替代。

## 11. 当前状态

当前“缺口修复＋条件风险门控”四臂已经完成筛查并被否决；PCT、Cotter 和 Kumar 原件已完成本地全文解析与结构化笔记。下一步先核验实现接口，再运行上述最小矩阵；封印年保持关闭。
