# Hugging Face 数据卡草案

> 适用仓库：`<归属>/malicious-traffic-llm-reproducibility`。
> 该仓库只提供处理代码、哈希、清单和聚合统计，不提供原始或逐行流量数据。由于项目代码尚未确定软件许可证，元数据暂用 `license: other`。

---

pretty_name: 恶意流量大模型复现协议与制品清单
license: other
task_categories:

- text-classification
  tags:
- cybersecurity
- network-intrusion-detection
- reproducibility
- data-provenance
- dataset-manifest

---

# 恶意流量大模型复现协议与制品清单

## 仓库内容

本仓库用于复现恶意流量生成式分类探针的数据审计、统一字段映射、分组划分、固定采样和制品清单生成流程。

仓库包含：

- GeNIS 与 HIKARI-2021 的字段适配代码。
- GeNIS 会话和时间审计代码。
- GeNIS 混合前向划分代码与聚合计划。
- 数据来源文件的大小、MD5 或 SHA-256。
- 不含地址、端口和原始 FlowID 的聚合清单。
- 固定提示词序列化和严格标签解析所需的字段契约。

仓库不包含：

- 原始 ZIP、CSV、PCAP、Zeek、CICFlowMeter 或系统日志。
- 逐行训练、验证和测试 JSONL。
- 会话级分配明细、预测明细或可回连到源行的样本标识。
- 模型权重、服务器连接信息、访问令牌和实验平台原始日志。

## 第三方数据来源

### GeNIS 1.0.0

- 官方记录：<https://doi.org/10.5281/zenodo.14919237>
- 许可：CC BY 4.0
- 使用文件：`2-flows.zip`
- 文件大小：380,755,720 字节
- MD5：`063b7a2ec6e6b73cc302151d2b3ba6d7`
- SHA-256：`72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30`
- 本项目修改：选择 10 秒窗口；映射八个共有流量字段；生成会话哈希、前向划分计划、聚合统计和固定样本清单。

### HIKARI-2021 1.4.0

- 官方记录：<https://doi.org/10.5281/zenodo.6463389>
- 许可：CC BY 4.0
- 使用文件：`ALLFLOWMETER_HIKARI2021.csv.zip`
- 文件大小：68,403,081 字节
- MD5：`d7d9e277fe4a66cb00764d7f91a810dd`
- SHA-256：`ba09d35269566fd2f269871043b24e7d8e372bc4a47e9c2027729e5ff2e660e0`
- 本项目修改：映射八个共有流量字段；使用端点对代理分组；执行固定预算平衡采样。

端点对只是代理分组，不能替代原始 PCAP 捕获会话，因此 HIKARI 只承担次级诊断证据。

### DEDALE 2.0

- 官方记录：<https://doi.org/10.57745/Y5JLDG>
- 官方说明：<https://dedale.inria.fr/download.html>
- 许可：CC BY 4.0
- 已完整核验文件：`cicflowmeter_orange_dmz.zip`
- 文件大小：279,861,801 字节
- MD5：`1dcf7d161f595c0d11c186d7255a5e75`
- SHA-256：`9b6438242bb3c4a282f3ef16810735335c859ac0c7907be27df246bca65b14a3`

DEDALE 的 Zeek DMZ 归档尚未完整下载，因此没有进入处理或清单。DEDALE 在完成 Zeek 标签关联前不进入模型训练，只计划用于时间外推和长期 APT 外部验证。

## 统一字段

`canonical_core_v1` 固定包含：

1. `total_packets`
2. `total_bytes`
3. `packet_length_mean`
4. `packet_length_min`
5. `packet_length_max`
6. `iat_mean_ms`
7. `packet_rate`
8. `byte_rate`

缺失值保留为 `None`，序列化时写为 `NA`，不静默填零。

## GeNIS 划分协议

- 对可划分攻击子类采用会话完整、按会话起始时间前向、带时间清除区的训练、验证和测试划分。
- `dos-icmp`、`dos-pushack` 和 `dos-udp` 不强行拆分，分别作为完整未见攻击场景域外测试。
- 原始 FlowID 经过 BLAKE2b 生成 32 位十六进制会话标识，不写入原始地址或端口。
- 时间、源文件名、会话标识和攻击子类只用于划分与审计，不进入模型提示词。

## 使用方式

1. 从上述官方记录下载数据，不从本仓库获取镜像。
2. 对照本仓库 SHA-256 验证文件版本。
3. 根据 `processing/flow_probe/` 中的适配器生成统一样本。
4. 先生成完整分组划分和审计清单，再执行固定预算采样。
5. 保存随机种子、源文件哈希、标签分布、缺失率、分组依据和证据等级。

## 许可与署名

- GeNIS、HIKARI-2021、DEDALE 2.0 分别保留原作者、官方记录和 CC BY 4.0 许可。
- 本仓库的派生清单标明了字段选择、哈希、聚合、划分和采样等修改。
- 处理代码许可证由项目权利人另行确定；在确定前，公开可见不等于获得复用授权。
- 本仓库不暗示第三方数据作者认可、赞助或验证本项目模型。

## 已知限制

- GeNIS 当前仍在完成正式混合防泄漏划分和多随机种子裁决。
- HIKARI 汇总 CSV 缺少可靠的捕获会话分组字段。
- DEDALE 标签主要附在 Zeek 连接日志，CICFlowMeter 表需要额外关联。
- 数据集均来自受控或仿真环境，不能代表全部真实网络、组织、协议和攻击分布。
- 任何高分都必须结合自然类别比例、未见场景、时间外推和跨数据集证据解释。
