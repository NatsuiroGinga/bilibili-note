# Hugging Face 发布审计笔记

## 来源

### 仓库内部来源

- `output/开题改进交接文档.md`
- `.Codex/docs/2026-07-19-第一创新点收敛实验计划.md`
- 待审计的本地运行目录、代码与数据清单

### 外部来源

- [GeNIS Zenodo 1.0.0](https://zenodo.org/records/14919237)：官方记录标记为 CC BY 4.0。
- [HIKARI-2021 Zenodo 1.4.0](https://zenodo.org/records/6463389)：官方记录标记为 CC BY 4.0。
- [DEDALE 2.0 数据仓库](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi%3A10.57745%2FY5JLDG)：自定义条款正文实际指定 CC BY 4.0。
- [DEDALE 下载与许可页](https://dedale.inria.fr/download.html)：明确允许以任何形式再分发、再发布和镜像，但必须引用数据集并链接该页。
- [CC BY 4.0 正文](https://creativecommons.org/licenses/by/4.0/legalcode)：允许复制、分享和制作改编材料；再发布时需要保留署名、许可链接并标明修改。
- [Qwen3-1.7B 模型页](https://huggingface.co/Qwen/Qwen3-1.7B)：基础模型许可为 Apache 2.0。
- [Hugging Face 模型卡规范](https://huggingface.co/docs/hub/model-cards)：模型仓库使用带元数据的 `README.md`，应说明数据、训练、评估、用途与限制。
- [Hugging Face 数据卡规范](https://huggingface.co/docs/hub/datasets-cards)：数据集仓库使用带元数据的 `README.md`，应说明内容、许可、偏差与责任边界。

## 服务器条件

- 本机：`HF_TOKEN` 未设置，`hf` 1.23.0 可用。
- 服务器：加载 `~/.vimrc` 后 `HF_TOKEN` 已设置，`hf` 与 `fd` 不可用。
- 服务器访问 `https://huggingface.co` 超时，`curl` 状态码 000、退出码 28。
- Hugging Face 用户名与组织归属未能通过官方接口确认。
- 结论：不创建仓库，不上传，不安装新工具；等待网络恢复并确认归属。

## 适配器核心清单

公共服务端前缀：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/`。

| 运行                                | `adapter_config.json` SHA-256                                      | `adapter_model.safetensors` 大小 | 权重 SHA-256                                                       | 判断                                                            |
| ----------------------------------- | ------------------------------------------------------------------ | -------------------------------: | ------------------------------------------------------------------ | --------------------------------------------------------------- |
| `smoke-qwen3-1.7b-seed42`           | `e1de83db727d04f6aa2e8062d42ff15e867a962a0b592381353efa695cedc9c2` |                       34,917,504 | `d6935dedc6044cef37a03d2255ed0e36957518b1c3a6fb0bd2e369365f5ec452` | HIKARI 烟雾运行，宏平均 F1 为 0.3333，不发布                    |
| `pilot-qwen3-1.7b-seed42`           | `2ec7f3ce6dc99d40ed393bea129ed10cd61ef902dbe758fb0429b346b446eb78` |                       34,917,504 | `655c5a95bc2ea4ae061d1053b34207425eca8e8d85cca2d1cb26b018f7d7a490` | HIKARI 早期未标准跟踪运行，不优先发布                           |
| `tracked-pilot-qwen3-1.7b-seed42`   | `77b4bdaa50e29170f7c479524f7273fabc7c8cfb6bae8011d9b8bbd9f2966cc7` |                       34,917,504 | `ed28bb6cdae10f65f583e0dd47c4acae36e168484dd980f015c09bd7d69b38ea` | HIKARI 次级预览候选，宏平均 F1 为 0.9800                        |
| `genis-10s-smoke-qwen3-1.7b-seed42` | `7751a9e8a08a6514dc858afebcb01d6e5834a3ed0b6e13b196f669c581e4f9c1` |                       34,917,504 | `39a5a85c79fffec702aaad437c1d6425d204290c92a80eec54cce020c459a861` | 首选预览候选，宏平均 F1 为 1.0000，但仅为 200/50/100 小样本探针 |

四份适配器均为 LoRA，`r=16`、`lora_alpha=32`、`lora_dropout=0.05`，目标模块覆盖注意力投影和前馈投影。四份 `adapter_config.json` 都把 `base_model_name_or_path` 写成服务器绝对路径，上传前必须在副本中改为 `Qwen/Qwen3-1.7B` 并重新计算 SHA-256。

## 分词器比对

以 GeNIS 适配器与服务器 Qwen 基座目录比对：

- `merges.txt`、`tokenizer.json`、`vocab.json` 与基座哈希相同。
- `added_tokens.json`、`chat_template.jinja`、`special_tokens_map.json` 在基座目录无同名文件。
- `tokenizer_config.json` 与基座不同，且可能包含保存时路径。
- 最小发布包不上传任何分词器文件，加载时直接使用 `Qwen/Qwen3-1.7B` 的分词器。
- `training_args.bin` 不属于推理必需文件，也不进入发布包。

## 第三方原始归档

| 数据集            | 服务器文件                                    |            字节数 | MD5                                | SHA-256                                                            | 发布策略                               |
| ----------------- | --------------------------------------------- | ----------------: | ---------------------------------- | ------------------------------------------------------------------ | -------------------------------------- |
| GeNIS 1.0.0       | `GeNIS-2025/2-flows.zip`                      |       380,755,720 | `063b7a2ec6e6b73cc302151d2b3ba6d7` | `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` | CC BY 4.0 允许再分发，但不镜像原始数据 |
| HIKARI-2021 1.4.0 | `HIKARI-2021/ALLFLOWMETER_HIKARI2021.csv.zip` |        68,403,081 | `d7d9e277fe4a66cb00764d7f91a810dd` | `ba09d35269566fd2f269871043b24e7d8e372bc4a47e9c2027729e5ff2e660e0` | CC BY 4.0 允许再分发，但不镜像原始数据 |
| DEDALE 2.0        | `DEDALE-2.0/cicflowmeter_orange_dmz.zip`      |       279,861,801 | `1dcf7d161f595c0d11c186d7255a5e75` | `9b6438242bb3c4a282f3ef16810735335c859ac0c7907be27df246bca65b14a3` | CC BY 4.0 允许再分发，但不镜像原始数据 |
| DEDALE 2.0        | `DEDALE-2.0/zeek_orange_dmz.zip`              | 审计时 93,322,696 | 未完成                             | 未完成                                                             | 部分文件，禁止上传和使用               |

## 本地候选文件清单

以下哈希针对当前源文件。任何清理、重命名或格式化都会改变哈希，上传前必须重新生成最终清单。

| 文件                                                          | 字节数 | SHA-256                                                            |
| ------------------------------------------------------------- | -----: | ------------------------------------------------------------------ |
| `src/flow_probe/adapters/base.py`                             |  3,002 | `b85f8f0c899a599f2b2c30a2903181a1fe8e0160d902fb3dce9dda30569c9bff` |
| `src/flow_probe/adapters/genis.py`                            |  3,174 | `7a9f10017e03565513a74e67f133ba5ab3ea7e0b0fe8a8208ab4dd38ab855917` |
| `src/flow_probe/adapters/hikari.py`                           |  2,375 | `c2ba10ea14190552dde0fa0168079c5b501137b4e4031ea0a52efed4d88702ab` |
| `src/flow_probe/schemas.py`                                   |  1,914 | `46939e71969c17c3a81bab3d651915be8d144f136f0cc625c9bb79a9d6a7fe0b` |
| `src/flow_probe/genis_audit.py`                               |  9,910 | `19be764c63edf8df845523ccd6c8a3f9a253b686fd2e0c15f2a5055a8a1d47af` |
| `src/flow_probe/genis_forward_split.py`                       | 23,581 | `73924911b580f7cc99c9b9acd28c3f26914e6d4ad758d76a280d7f9639cc17a8` |
| `src/flow_probe/manifest.py`                                  |  2,343 | `6d4f35c691f8ed20ecbfb58517b2440181ac88fd0faf3d60146be4b4c146ee63` |
| `src/flow_probe/prepare.py`                                   |  5,102 | `c266c5b127920d8667bc7df7d9a8168fd57f0836a5dc50714301ff88543a724b` |
| `src/flow_probe/sampling.py`                                  |  6,279 | `2771c626ee90b7792f31bc247d3a97767cd73eb756b481489a01fc66ceb46749` |
| `src/flow_probe/serialize.py`                                 |    928 | `73cd9c1403932117acb7c202db86d35e20be5c87a0baff3cd3ffc3d71a55e305` |
| `src/flow_probe/split.py`                                     |  6,647 | `2c40f03ecda90bf112737b17da50ecb223d9a4becb7b7d05f99a4f80d9ab217a` |
| `configs/genis_smoke_qwen3_1_7b.yaml`                         |    876 | `47bf9fc028fda970584b6f9ce5ecc4832b1d5ea429a5d844336fe331f095b6e5` |
| `configs/smoke_qwen3_1_7b.yaml`                               |    806 | `dd66325640caa0a221dfdce5deac629eef97727c0d12e2280020458ab08ec0cf` |
| `runs/genis-10s-smoke-qwen3-1.7b-seed42/training_config.yaml` |    842 | `ee2fd7fe8ab66225f1e172b879f1672a6aab1e1aa5dc516d1400fefb506b216d` |
| `dataset_provenance.json`                                     |    487 | `c542d5f70d96a30779f6811352fca141ab42b1a194981d2f35999e23f8a92484` |
| `sample_manifest.json`                                        |  1,086 | `645d55537bf987168cdf1fb4a6c8ee90c4265d29f0995c7eea8f87631826adec` |
| `training_summary.json`                                       |    660 | `493b8bab2459a817c13eee6c232ad3f47d605f07c642308300b582f3fb0382f5` |
| `evaluation_summary.json`                                     |    882 | `c7d36eec5d3748b13a504292caa755eac992d928477e9530ff3a9e557225fd40` |
| `audit.json`                                                  |  8,555 | `42a1afe59b65b598c9d43f5084d482b9ecc0ef561d769009b46c1cea93354513` |
| `plan_summary.json`                                           |  4,590 | `0f2bc0df3d6370c29d2bf286852ef4ca0b4581c56959777da32a038b1533cb7a` |

本地公共前缀为 `thesis/experiments/llm_probe/`。其中 `training_summary.json`、`evaluation_summary.json`、两个训练配置和 `audit.json` 含本地或服务器路径，必须清理后再上传；`plan_summary.json` 已只记录源文件名、大小和哈希。

## 明确排除项

- Qwen 基座权重和缓存。
- 三个第三方数据集的原始归档、解压 CSV、PCAP、Zeek 和逐行训练 JSONL。
- `session_assignments.jsonl`：41,056,778 字节，包含会话级时间与攻击子类，当前发布收益不足。
- `predictions.jsonl`：包含可回连到源文件名和行号的 `sample_id`，当前只发布聚合指标。
- SwanLab 原始二进制日志、调试日志、下载日志、控制台日志和截图。
- 分词器副本、`training_args.bin`、检查点、优化器状态和任何凭据。

## 初步边界

- 允许候选：自有训练适配器、训练与评估配置、处理脚本、不可逆聚合统计、自有预测结果、无敏感信息的制品清单。
- 默认禁止：Qwen 基座权重、第三方原始流量、可重构原始记录的逐行派生数据、凭据、服务器连接信息、未核验许可的镜像数据。

## 许可裁决

- GeNIS、HIKARI-2021、DEDALE 2.0 均明确采用 CC BY 4.0，允许再分发和改编。
- 再发布派生清单时必须列出作者或数据集名称、官方链接、CC BY 4.0 链接，并标明本项目完成了字段选择、划分、聚合或哈希处理。
- Qwen3-1.7B 基座采用 Apache 2.0，只上传适配器，不上传基座权重。
- 当前项目没有根级或 `llm_probe` 级软件许可证。处理代码公开上传前需要权利人选择许可证；建议 Apache 2.0，但本次不代替权利人作许可决定。
- 本笔记是发布工程审计，不构成法律意见。
