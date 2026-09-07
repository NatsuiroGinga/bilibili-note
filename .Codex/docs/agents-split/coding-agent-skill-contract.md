# 编码代理 Skill 收据合同

## 适用与边界

只适用于新增或修改生产代码的子代理交付。收据证明可观察的读取记录、声明清单、文件范围和验证收据；**不能证明代理理解或逐项正确执行 Skill**，主代理仍对代码和真实运行结论负责。缺少收据只退回原代理补齐，不新增文字复审轮次或阻塞已满足科学门禁的实验。

## 简报与映射

简报必须指定 `required_skills` 和唯一 JSON 收据路径。按任务动态选择，不得让所有任务加载全部 Skill：

| 情形 | 必需 Skill |
|---|---|
| 日常生产编码 | `daily-coding` |
| 缺陷修复 | `systematic-debugging`、`bug-detective` |
| PyTorch 模型/训练 | `pytorch-patterns` |
| 第三方 API | 当前版本官方接口核验（记录库、版本、来源和签名） |

开始修改前，代理记录每个 Skill 的绝对路径、内容 SHA256、读取时刻和关键清单证据；交付时记录拥有文件、实际改动文件、验证命令及退出码、真实运行证据或不适用理由。

## 验收

主代理只运行一次：

```sh
/opt/miniconda3/envs/rwkv/bin/python tools/verify_agent_skill_receipt.py --receipt <路径>
```

验证器不执行代码、不访问网络；它核对当前 Skill 哈希、必填字段、`actual_changed_files` 是 `owned_files` 子集、验证命令退出码为零，以及真实运行证据或不适用理由。失败时退回原代理；通过不等于科学结论或代码正确。

## Hook 边界

当前运行时没有可靠的 `spawn_agent` 简报解析前拦截。Hook 最多提示，不能自动保证代理已读取 Skill；以简报和收据验收为唯一可审计机制。
