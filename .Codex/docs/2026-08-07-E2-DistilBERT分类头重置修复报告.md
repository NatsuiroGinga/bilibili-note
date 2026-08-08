# E2 DistilBERT 分类头重置修复报告

## 结论

已修复 E2 DistilBERT 正式启动前的分类头重置误判。基础模型来源门禁仍拒绝带序列分类头的检查点；加载模型后仍以冻结种子显式重置 `pre_classifier` 与 `classifier`。修复仅取消“重置前后参数摘要必须不同”的错误要求，并把重置是否执行、参数摘要是否变化及前后摘要写入审计记录。

## 任务边界

- 修改 `thesis/experiments/llm_probe/src/flow_probe/e2_distilbert.py`。
- 修改 `thesis/experiments/llm_probe/tests/test_e2_distilbert.py`。
- 新增本报告。
- 未修改模型、数据、种子、训练预算、初始化器、初始化顺序或最终初始化分布。
- 未触碰 E2-A、E2-S、E2-P、E2-X 的文件、运行目录或进程。

## 根因与假设

基础模型已由 `_validate_base_model_binding` 限制为 `DistilBertForMaskedLM` 或 `DistilBertModel`，不能复用序列分类检查点中的分类头。`from_pretrained` 在固定种子 42 下为缺失的分类头创建新参数；后续显式重置使用相同初始化器和相同种子时，可以合法地产生相同参数摘要。旧实现把摘要相等误判为未执行重置并抛出异常。

单一可证伪假设为：只要保留显式初始化调用并把摘要变化改为审计事实，而不是成功条件，同种子相同摘要场景就应被接受，其他来源检查点和分类头结构门禁不受影响。

## 测试驱动记录

先新增 `test_classification_head_reset_accepts_same_seed_identical_digest`。该测试先用种子 42 和模型初始化器创建两个分类头组件，再调用真实的 `_reset_classification_head` 并继续使用种子 42；预期前后摘要相等，同时审计结果记录重置已经执行且摘要未变化。

按任务限制，未在本机执行 `pytest`。红灯由旧代码路径静态确认：测试构造的前后摘要相等时，旧实现会命中“分类头显式重置后参数摘要未变化”异常。生产修复完成后，同一测试需要在服务器执行下列唯一目标命令确认转绿：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe && uv run --no-sync pytest -q tests/test_e2_distilbert.py -k classification_head_reset_accepts_same_seed_identical_digest
```

服务器目标测试尚未由本实现代理执行，因此本报告不把它标记为已通过。

## 生产修复

- 保留 `torch.manual_seed(seed)`。
- 保留对 `pre_classifier` 与 `classifier` 的逐组件显式初始化。
- 保留初始化前后的 SHA-256 摘要。
- 删除摘要相等时抛错的分支。
- 新增 `reset_performed=True`，仅在两个组件均完成显式初始化后返回。
- 新增 `parameter_digest_changed`，如实记录前后摘要是否不同；摘要相等不再等同于重置失败。

## 验证状态

- 本机 `pytest`：未执行，符合任务限制。
- 格式化：未执行，符合任务限制。
- 远程登录与同步：未执行，符合任务限制。
- Python 语法检查：已通过，两个目标 Python 文件均可被 `ast.parse` 解析。
- 服务器唯一目标测试：待控制代理执行上述命令。

## 遗留风险

服务器目标测试通过前，只能确认实现与测试的静态合同一致，不能宣称运行验证完成。正式启动器仍应保存 `base_model_binding` 与 `classification_head_initialization`，从而共同证明来源检查点不含可复用分类头，并记录显式重置的模式、种子、组件和摘要。
