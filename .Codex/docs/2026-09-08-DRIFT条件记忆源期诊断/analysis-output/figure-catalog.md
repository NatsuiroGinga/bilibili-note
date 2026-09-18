# DRIFT 条件记忆源期资格图件目录

## 图 1：候选相对 D0 的错误预测对数损失差

- 文件：`figures/figure-01-logloss-difference.pdf`。
- 目的：展示 DeepEmbed 与 Engram 在 T18/T19×良性/DGA 四个单元相对 D0 的成对差和 95% 区间。
- 数据：`result.json -> analysis.by_label.*.years.*.*.comparisons.versus_d0`。
- 读图重点：Engram 四格均低于 0；DeepEmbed 的良性 T19 和 DGA T18 跨 0。
- 决策含义：Engram 有增量错误预测信息，DeepEmbed 的跨类别跨年门失败。
- 限制：纵轴是诊断模型对数损失差，不是 DGA 检测性能增益。
- 题注必须说明：负值表示候选诊断特征更好；区间只量化固定预测集的 eSLD 抽样近似不确定性。

## 图 2：Engram DGA 方向与 family 中心化敏感性

- 文件：`figures/figure-02-engram-direction.pdf`。
- 目的：并列显示 DGA 偏秩相关和 family 内中心化相关的符号。
- 数据：`result.json -> analysis.partial_rank.1.engram` 与 `analysis.family_centered.*.engram`。
- 读图重点：DGA 多个信号三年为稳定负相关；family 中心化的支持和语义碰撞在 T19 翻转。
- 决策含义：不得把 Engram 的对数损失优势事后改写为预注册的正向病灶。
- 限制：family 中心化面板包含当年新 family，只作描述，不单独裁决。
- 题注必须说明：正方向才符合既定“低支持／惊异／碰撞增大错误”假设；负值不能在看数后反转解释。
