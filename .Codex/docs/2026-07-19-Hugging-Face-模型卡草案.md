# Hugging Face 模型卡草案

> 适用仓库：`<归属>/qwen3-1.7b-genis-10s-qlora-preview`。
> 发布前必须确认归属和适配器许可证，并把所有 `<归属>` 占位符替换为实际值。建议许可证为 Apache 2.0，但本草案不代替权利人作许可决定。

---

base_model: Qwen/Qwen3-1.7B
base_model_relation: adapter
library_name: peft
license: apache-2.0
pipeline_tag: text-generation
tags:

- peft
- lora
- qlora
- qwen3
- cybersecurity
- network-intrusion-detection
- research-preview

---

# Qwen3-1.7B GeNIS 恶意流量 QLoRA 研究预览

## 模型简介

本仓库提供基于 `Qwen/Qwen3-1.7B` 的 PEFT LoRA 适配器，用于根据八个统一流量统计字段生成严格二分类 JSON：

- `{"label":"benign"}`
- `{"label":"malicious"}`

本制品只用于验证生成式恶意流量分类管线的可行性。它不是论文最终方法，也不是生产级入侵检测器。

## 基础模型

- 基础模型：`Qwen/Qwen3-1.7B`
- 基础模型许可：Apache 2.0
- 参数高效微调：QLoRA
- LoRA 秩：16
- LoRA 缩放系数：32
- LoRA 丢弃率：0.05
- 思考模式：关闭

本仓库不包含 Qwen 基座权重。使用者需要从基础模型仓库单独加载模型和分词器。

## 训练数据

训练使用 GeNIS 1.0.0 的 10 秒流表示。官方数据记录：

- 数据集：GeNIS: GECAD Network Intrusion Scenarios
- 版本：1.0.0
- DOI：<https://doi.org/10.5281/zenodo.14919237>
- 许可：CC BY 4.0

本次预览运行使用 200 条平衡训练样本、50 条平衡验证样本和 100 条平衡测试样本，随机种子为 42。模型输入不包含数据集名、源文件、IP、端口、时间戳、FlowID、场景名或标签字段。

## 输入格式

字段顺序固定为：

1. `total_packets`
2. `total_bytes`
3. `packet_length_mean`
4. `packet_length_min`
5. `packet_length_max`
6. `iat_mean_ms`
7. `packet_rate`
8. `byte_rate`

提示词格式：

```text
任务：判断以下网络流是良性还是恶意。
流量：total_packets=...;total_bytes=...;packet_length_mean=...;packet_length_min=...;packet_length_max=...;iat_mean_ms=...;packet_rate=...;byte_rate=...
只输出 JSON：{"label":"benign"} 或 {"label":"malicious"}
```

缺失值写为 `NA`。输出只接受单键 JSON 对象，不修复解释文本、代码围栏、额外键或未知标签。

## 加载示例

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model_id = "Qwen/Qwen3-1.7B"
adapter_id = "<归属>/qwen3-1.7b-genis-10s-qlora-preview"

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype="auto",
    device_map="auto",
)
model = PeftModel.from_pretrained(model, adapter_id)

prompt = (
    "任务：判断以下网络流是良性还是恶意。\n"
    "流量：total_packets=12;total_bytes=4096;packet_length_mean=341.333;"
    "packet_length_min=64;packet_length_max=1500;iat_mean_ms=3.2;"
    "packet_rate=18.75;byte_rate=6400\n"
    '只输出 JSON：{"label":"benign"} 或 {"label":"malicious"}'
)
messages = [{"role": "user", "content": prompt}]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=16, do_sample=False)
prediction = tokenizer.decode(
    outputs[0, inputs["input_ids"].shape[1] :],
    skip_special_tokens=True,
)
print(prediction)
```

## 预览评估

| 指标             |   数值 |
| ---------------- | -----: |
| 测试样本数       |    100 |
| 宏平均 F1        | 1.0000 |
| 恶意召回率       | 1.0000 |
| 误报率           | 0.0000 |
| 严格 JSON 有效率 | 1.0000 |

这些数值只对应单随机种子、小样本、平衡测试集，不代表自然类别比例、未见攻击、跨数据集或生产环境性能。满分结果不能用于宣称方法优越性。

## 适用范围

- 复现生成式二分类提示词与严格 JSON 解析管线。
- 检查 PEFT 适配器加载、量化微调和短推理流程。
- 作为后续防泄漏、多随机种子和跨数据集实验的预览基线。

## 限制与风险

- 只完成随机种子 42，尚未完成 42、43、44 多随机种子验证。
- 当前训练集只有 200 条样本，测试集只有 100 条平衡样本。
- 当前结果不能证明 PINN 机制、未知攻击泛化或长期 APT 检测能力。
- GeNIS 正式混合防泄漏协议尚在收敛，现有测试不能替代正式 H1 结论。
- 生成式模型可能产生非法 JSON、漏报、误报或分布外错误。
- 不得将输出直接用于自动封禁、隔离、取证归责或其他高影响安全操作。

## 数据署名

GeNIS 由 Miguel Silva、Daniela Pinto、João Vitorino、José Gonçalves、Eva Maia 和 Isabel Praça 发布，采用 CC BY 4.0。本项目只使用其 10 秒流表示进行字段映射、分组、采样和训练；未在本仓库再发布原始流量。

## 许可证

适配器拟采用 Apache 2.0，基础模型许可见 `Qwen/Qwen3-1.7B`。训练数据的权利和署名义务仍由 GeNIS 的 CC BY 4.0 条款约束。
