# Task 1：生成 C10 配置

## 本任务全局约束（逐字取自计划）

- `run_tier` 必须为 `screening_only`；`checkpoint.formal_resume_eligible` 必须为 `false`
  （宿主 `:418` 强制：筛选检查点不得正式续训）。
- `mechanism.entity_aggregation` 开启时，键集**只能**是
  `{alpha, enabled, kind, numeric_provenance}`（宿主 `:314` 白名单，多一个键即拒）。
- `alpha` 必须严格等于已冻结的 `0.5`（宿主 `:325`，且明文禁止按实验读数回调）。
- `evaluation.target_reads` 必须为 `0`；全程不得读取 LSPR24。
- `width_profile` 为 `half`，骨干参数量断言 `240955`。
- **不得改动宿主 `.py` 任何一行**——本计划只新增配置与守护链条目。
- 提交用 `git commit -m "..." -- <精确路径>`，**绝不 `git add .`**，
  提交信息末尾**不得**有 Co-Authored-By 署名。

---

**Files**
- Create: `thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json`
- Read（不改）: 同目录 `ch3-ft-c00-halfwidth-screening-v1.json`、`ch3-ft-c11-halfwidth-screening-v1.json`

**Interfaces**
- Produces：新配置的 `science_identity_sha256`（任务 2 登记，任务 3 启动时核对）

- [ ] **步骤 1：以 C00 为底，取 C11 的 ETA 块**

用 Python 读两份配置并合成，**不要手写整份 JSON**（83 个字段手抄必错）：

```python
import json, pathlib
d = pathlib.Path("configs")
c00 = json.loads((d / "ch3-ft-c00-halfwidth-screening-v1.json").read_text(encoding="utf-8"))
c11 = json.loads((d / "ch3-ft-c11-halfwidth-screening-v1.json").read_text(encoding="utf-8"))

c10 = json.loads(json.dumps(c00))                      # 深拷贝，避免共享引用
c10["mechanism"] = {"entity_aggregation": json.loads(json.dumps(c11["mechanism"]["entity_aggregation"]))}
c10["identity"]["run_id"] = "ch3-ft-c10-halfwidth-screening-v1"
c10["identity"]["candidate_key"] = "entity-tail-aggregation-c10-dual-selection"
c10["identity"]["science_contract_version"] = c11["identity"]["science_contract_version"]
c10["evaluation"]["entity_aggregation"] = "entity_tail_mean_over_validation_flows"
c10["data"]["reuse_input_transform_from"] = "ch3-ft-c00-halfwidth-screening-v1"
c10["tracking"]["group"] = "ch3-ft-c10-halfwidth-screening-v1"
c10["paths"]["output_root"] = c00["paths"]["output_root"].replace("c00", "c10")

(d / "ch3-ft-c10-halfwidth-screening-v1.json").write_text(
    json.dumps(c10, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

**注意 `paths.output_root` 的替换**：若 C00 的该值不含字面 `c00`，
`replace` 会静默无效并让两个运行写进同一目录。**先打印确认再写**。

- [ ] **步骤 2：核对三处关键字段**

```python
import json
c10 = json.load(open("configs/ch3-ft-c10-halfwidth-screening-v1.json"))
assert c10["mechanism"]["entity_aggregation"]["enabled"] is True
assert c10["mechanism"]["entity_aggregation"]["alpha"] == 0.5
assert "entity_ranking" not in c10["mechanism"]            # z2=0
assert c10["evaluation"]["entity_aggregation"] == "entity_tail_mean_over_validation_flows"
assert c10["evaluation"]["target_reads"] == 0
assert c10["identity"]["run_tier"] == "screening_only"
assert c10["checkpoint"]["formal_resume_eligible"] is False
assert c10["model"]["width_profile"] == "half"
assert "c10" in c10["paths"]["output_root"]
print("九项断言通过")
```

预期：打印「九项断言通过」。任一断言失败即停下修配置，不要继续。

- [ ] **步骤 3：提交**

```bash
git commit -m "feat(ch3): add c10 halfwidth screening config" -- thesis/experiments/llm_probe/configs/ch3-ft-c10-halfwidth-screening-v1.json
```

---
