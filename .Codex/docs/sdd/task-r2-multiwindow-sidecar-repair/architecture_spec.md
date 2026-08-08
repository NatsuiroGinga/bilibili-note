# R2 因果多窗口物理旁路修复架构规格

日期：2026-08-03  
状态：实现前冻结规格  
范围：唯一一次 R2 多窗口结构修复，仅使用开发训练与开发验证，不读取最终测试  
执行边界：本规格为只读架构设计；不修改当前 v0 实验源码、配置、服务器进程或运行制品

## 1. 结论

本次修复采用五组同结构对照，而不是继续修补当前静态 `18 -> 768` 无界投影：

| 组 | 输入 | 作用 |
| --- | --- | --- |
| `T-A` | 全零 `[4,18]` 序列，旁路门关闭 | 新代码路径下的纯文本基础组 |
| `T-H` | 真实配对的因果原始历史 `[4,18]` | 等信息来源、等形状、等参数预算的历史基线 |
| `T-P` | 由同一原始历史派生且与样本正确配对的物理序列 `[4,18]` | 检验物理变换的样本特定增量 |
| `T-S` | 在同来源、同传输族、同路由、同划分内整段错配的物理序列 `[4,18]` | 保留物理序列联合分布，破坏样本对应关系 |
| `T-R` | 仅从开发训练物理序列统计生成的坐标随机序列 `[4,18]` | 保留一维边际，破坏跨字段、跨窗口结构 |

五组使用同一个因果编码器、同一个有界融合模块、相同参数量、相同 DistilBERT、相同文本、相同样本、相同划分、相同种子和相同 `192` 个优化步。每个“种子 × 组”必须是独立 Python 进程和独立 SwanLab 运行。

修复不得改变当前 v0 输出。旧 v0 仍由原配置和无 `--variant` 的兼容入口恢复；v1 使用新配置模式、新输入摘要和独立输出根。实现和审查可以与当前 v0 正式运行并行，v1 正式训练只能在完整 v0 十二组形成预注册 `NO_GO` 后启动。

## 2. 诊断与方法边界

当前 `T-P` 不是完整 R2 的 TCP、UDP、QUIC 专家实现，具体原因如下：

1. 当前旁路来自共享与 TCP/UDP 树回归器的静态代理，没有 QUIC 动力学专家。
2. 当前 TQH-C2 输入把同一个整流统计重复四次，未使用真实逐包时间历史。
3. 当前模型把队列、残差、不确定性、三个路由掩码和协议置信度一并送入未标准化线性层，掩码量级明显大于多数物理量。
4. 当前投影随机初始化并无界相加，优化开始前即可大幅扰动文本表征。
5. 当前按 `transport_family=UDP` 启用 UDP 专家，但协议表显示本试点的 `92` 条 UDP 承载样本全部为 `protocol_target=UNKNOWN`。

修复后的路由合同固定为：

- 共享专家对全部样本可用。
- TCP 专家仅由部署可观测的 `transport_family=TCP` 启用。
- UDP 承载无法仅凭本轮白名单字段可靠区分普通 UDP 与 QUIC，因此本试点的全部 UDP 承载只走共享专家，UDP 专家不启用。
- ICMP 和其他未支持协议只走共享专家。
- `protocol_target` 是训练期协议真值，只允许审计上述路由结果，禁止作为物化器或模型的路由输入。
- 本试点没有 qlog 或 QUIC 动力学真值，禁止启用或声称已经实现 QUIC 动力学专家。
- 路由决定和专家置信度停止梯度；DistilBERT 分类损失不得更新路由器或物理状态代理。
- 路由掩码、传输族和协议置信度不拼入可学习序列，不允许分类器把协议路由当作标签捷径。

因此，本修复只裁决“开发集上，因果物理变换是否提供超过原始历史和负对照的检测增量”，不能证明完整 R2/Qwen、UDP 动力学或 QUIC 动力学有效。

## 3. 建议文件范围

### 3.1 新增源码与配置

| 路径 | 责任 |
| --- | --- |
| `thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_sidecar.py` | 因果包窗、原始序列、前缀物理代理、归一化、负对照和物化校验 |
| `thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_fusion.py` | 同形状因果编码器、零初始化有界残差融合和融合诊断 |
| `thesis/experiments/llm_probe/configs/r2_multiwindow_sidecar_materialization_v1.yaml` | 一次性开发物化输入、摘要、窗口、字段、路由和辅助物理池合同 |
| `thesis/experiments/llm_probe/scripts/run_r2_multiwindow_sidecar_materialization.sh` | 确定性一次性物化入口，不启动训练 |
| `thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed42.yaml` | 种子 42 单组进程训练合同 |
| `thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed43.yaml` | 种子 43 单组进程训练合同 |
| `thesis/experiments/llm_probe/configs/r2_distilbert_multiwindow_seed44.yaml` | 种子 44 单组进程训练合同 |
| `thesis/experiments/llm_probe/scripts/run_r2_distilbert_multiwindow_probe.sh` | 顺序拉起十五个独立进程，维护启动器状态 |
| `thesis/experiments/llm_probe/src/flow_probe/r2_multiwindow_analysis.py` | 完成十五组后进行开发集离线统计，不读取最终测试 |

本次物化只处理已经解析的 `173,196` 行、`2,560` 个开发样本，预计制品小于 `10 MiB`，不扫描 PCAP，也不是生产热路径。因此允许复用现有 PyArrow 依赖完成一次性确定性派生，不为此新增 Rust 工具。若后续扩大到全量数据或进入重复在线生成，再另立任务迁移热路径；不得把该迁移混入本次唯一修复。

### 3.2 修改现有源码

仅修改 `thesis/experiments/llm_probe/src/flow_probe/r2_distilbert_sidecar_probe.py`，要求是向后兼容扩展，不得原位替换旧合同：

- 保留旧 `CONFIG_SCHEMA_VERSION`、`VARIANTS=(T-A,T-P,T-S,T-R)`、旧数据类、旧四组串行执行和旧输出读取能力。
- 新增 `MULTIWINDOW_CONFIG_SCHEMA_VERSION` 和 `MULTIWINDOW_VARIANTS=(T-A,T-H,T-P,T-S,T-R)`，不得复用旧模式版本字符串。
- 新配置必须显式携带 `probe_mode: multiwindow_v1`；旧配置未携带该字段时走完全相同的 v0 分支。
- v1 入口强制要求 `--variant`，一次只准备和执行一个组；v0 无 `--variant` 的行为保持不变。
- v1 保存新融合制品 `multiwindow_fusion.pt` 与 `multiwindow_fusion_config.json`，不得写旧 `sidecar_projection.pt`。
- v1 使用独立结构、运行绑定、检查点、收尾和汇总模式版本，旧收据只能只读校验，不能升级或覆盖。

### 3.3 不修改的文件与制品

- 不修改旧三个 `r2_distilbert_sidecar_probe_seed*.yaml`。
- 不修改旧 `scripts/run_r2_distilbert_sidecar_probe.sh`。
- 不修改旧静态 `tqhc2-pilot-sidecar.parquet`。
- 不修改双物化逐包源表和协议表。
- 不写入 `runs/r2-transformer-sidecar-probe/distilbert-v0/`。
- 不读取任何最终测试清单、最终测试特征或最终测试标签。

## 4. 冻结输入与因果窗口

### 4.1 源制品

主包表固定为：

```text
thesis/experiments/llm_probe/runs/data-frozen/
  r2-protocol-tqhc2-handoff-v0.build-a.partial/packet-observations.parquet
SHA-256 = 21168c943d7b9be043174a19cbde751c5cdb9c34b37e6902370998be88013991
```

协议路由表固定为：

```text
thesis/experiments/llm_probe/runs/data-frozen/
  r2-protocol-tqhc2-handoff-v0.build-a.partial/protocol.parquet
SHA-256 = 1c48b3437d5c17b0eb1524bc22856b1803b9dbb5d29b13b4f0593a7542b3560c
```

构建 B 的包表字节摘要与构建 A 完全相同，只作双物化证据，不得作为第二份训练样本。目录仍为 `.partial`，本修复只能称为哈希绑定的开发试点，不能称为正式发布数据。

当前 `2,560` 个开发样本全部可连接，共 `173,196` 个包；`(sample_id, packet_index)` 无重复。连接必须绑定 `sample_id`、原 `observation_sequence_sha256`、包表 SHA-256 和窗口模式版本。

### 4.2 唯一窗口定义

固定 `W=4`，按 `packet_index` 升序构造非重叠窗口：

```text
w0 = [0, 2)
w1 = [2, 4)
w2 = [4, 8)
w3 = [8, N_at_decision)
```

`N_at_decision` 仅表示分类决策时已经观测到的包数。禁止按整条流四等分，因为这种早期边界依赖尚未到达的最终包数。

顺序和时间合同如下：

- 唯一排序键是 `packet_index`。
- `causal_elapsed_us` 由 `max(delta_time_us,0)` 累加。
- `relative_time_ns` 只作审计，不参与重排。当前已有 `54` 条流、`75` 处回退，最小回退 `-290000 ns`。
- 窗口首包的 `delta_time_us` 保留其相对前一包的已观测间隔。
- `packet_rate` 和 `byte_rate` 的分母是本窗 `delta_time_us` 之和；分母为零时置缺失，不填数值零。
- 空窗连续值为空，数值张量化后填零，同时保留缺失掩码与 `window_valid=0`。
- 不复制前窗，不重复整流统计，不删除短流。`58` 条短流按原划分保留。
- 八字段跨窗必须精确重构整流包数和总字节；均值按有效计数加权后必须与整流统计一致。

### 4.3 原始窗口字段

每窗只从 `packet_index`、`delta_time_us` 和 `network_length_bytes` 派生下列八个字段：

```text
total_packets
total_bytes
packet_length_mean
packet_length_min
packet_length_max
iat_mean_ms
packet_rate
byte_rate
```

每个字段带一个同名 `*_missing`。为遵守唯一修复中“不得修改旁路维度”的合同，每窗继续保持 `18` 维，最后两个位置是模式绑定的恒零保留位，不携带新信息：

```text
raw_sequence: float32 [N, 4, 18]
  [:, :, 0:8]  = 八个连续值
  [:, :, 8:16] = 八个二值缺失掩码
  [:, :, 16:18] = 两个恒零保留位
window_valid: bool [N, 4]
```

保留位必须在物化、加载和模型入口三处断言精确为零，不得在本轮改作新增特征。

`direction`、载荷长度、TCP 标志、突发编号和 `25` 个 QUIC 线图像字段均不进入本轮模型。`sample_id` 只作连接；标签、`profile`、采集单元、场景、来源路径和划分标识只作选择或审计，不进入模型张量。

## 5. 物理序列派生

### 5.1 不得复用旧静态向量

禁止把旧 `18` 维静态旁路复制四次。旧估计器一次读取完整四窗并同时预测全部状态，较早状态可能依赖较晚窗口，也不满足严格因果要求。

新物理代理必须在已有 ns-3 辅助池上按前缀训练四个固定预测器。对于窗口 `t`，预测器输入只能是 `raw_sequence[:,0:t+1,:]`，不得读取 `t+1` 及以后窗口。辅助池划分继续使用原有 `12` 个拟合组和 `4` 个校准组，禁止因 TQH-C2 验证结果改变组、模型或超参数。

固定回归器保持当前先导设置：

```text
MultiOutputRegressor(
  HistGradientBoostingRegressor(
    learning_rate=0.05,
    max_iter=160,
    max_leaf_nodes=31,
    min_samples_leaf=12,
    l2_regularization=1.0,
    random_state=20260803
  ),
  n_jobs=1
)
```

物理真值的尺度也必须因果。禁止沿用旧实现中“取当前完整四窗 `truth_capacity_integral_link_bytes.max()`”的逐序列尺度，因为窗口 `t` 的目标会由 `t+1` 以后窗口决定。新代理先仅从 ns-3 十二个辅助拟合组冻结一个全局常量：

```text
auxiliary_target_scale
  = max(1, 所有辅助拟合窗口的 truth_capacity_integral_link_bytes 最大值)
```

所有拟合与校准窗口的队列起点、队列终点、入队量和出队量都除以同一个 `auxiliary_target_scale`。该常量不得读取四个辅助校准组、TQH-C2 或最终测试，并写入物化清单。这样四个前缀和相邻队列锚点处于同一单位，`boundary_residual` 可直接计算。

每个前缀预测器输出当前窗口四个量：上述共同尺度下的队列起点、队列终点、入队量、出队量。共享预测器使用全部辅助拟合组；TCP/UDP 专家只使用各自辅助拟合样本。TQH-C2 本试点的专家混合固定为：

```text
transport_family == TCP: 0.5 * shared + 0.5 * tcp
transport_family != TCP: 仅使用 shared
UDP 专家: 只保留辅助拟合证据，本试点不启用
QUIC 专家: 本试点不可用且禁止启用
```

混合后的队列起点、队列终点、入队量和出队量逐项截断到非负区间，但不设置由开发验证选择的上界。守恒残差和边界残差在非负状态量生成后计算并保持有符号。

物理代理和混合在离线物化阶段完成，不成为 DistilBERT 计算图的一部分。

### 5.2 物理窗口张量

每个有效窗口 `t` 形成八个连续物理量：

```text
estimated_queue_start_t
estimated_queue_end_t
normalized_enqueued_t
normalized_dequeued_t
normalized_conservation_residual_t
normalized_boundary_residual_t
state_uncertainty_start_t
state_uncertainty_end_t
```

其中：

```text
conservation_residual_t
  = queue_end_t - queue_start_t - enqueued_t + dequeued_t

boundary_residual_0 = 0
boundary_residual_t = queue_start_t - queue_end_(t-1), t > 0
```

状态不确定性由辅助校准组的状态误差尺度与共享/适用专家分歧构造。对每个前缀 `t`、队列锚点 `a ∈ {start,end}` 和路由类 `c`，固定计算：

```text
rmse_(t,a,c) = sqrt(mean((q_hat_blended - q_truth)^2))
disagreement = abs(q_hat_shared - q_hat_applicable_expert)
calibration_score = abs(q_hat_blended - q_truth) + disagreement
scale_(t,a,c) = max(quantile(calibration_score, 0.95), 1e-6)
uncertainty = clip((rmse_(t,a,c) + disagreement) / scale_(t,a,c), 0, 1)
```

`shared_only` 的 `disagreement` 恒为零，并使用共享预测器在全部辅助校准组上的 `rmse` 与 `scale`。未知协议不能伪造不存在的专家分歧。所有量只由 ns-3 辅助校准组确定；TQH-C2 开发训练和开发验证标签均不得参与不确定性标定。窗口级 `physics_uncertainty_t` 固定为起点与终点不确定性的算术均值。

八个连续物理量各带一个缺失掩码。物理张量同样保留原旁路宽度 `18`：

```text
physics_sequence: float32 [N, 4, 18]
  [:, :, 0:8]  = 八个连续物理量
  [:, :, 8:16] = 八个二值缺失掩码
  [:, :, 16:18] = 两个恒零保留位
physics_valid: bool [N, 4]
physics_uncertainty: float32 [N, 4]  # 未缩放且位于 [0,1]，只供停止梯度门使用
```

空窗不得由物理代理生成伪状态。每个窗口的物理输出只依赖该窗口及此前窗口。冻结辅助物理代理只读取共同物理单位下、未做 TQH 分类缩放的每窗前 `16` 个真实字段，不读取两个恒零保留位；物化清单必须记录四个代理前缀输入维度 `16/32/48/64`、共同目标尺度和对应模型摘要。

### 5.3 跨域限制

ns-3 辅助数据使用固定 `0.1 s` 窗口，而 TQH-C2 主定义使用固定包序窗口。虽然八字段名称与单位一致，这仍是输入域变化。物化必须报告每字段超出辅助拟合范围的比例和每窗口分位数，但不得根据开发验证结果调整窗口、裁剪阈值或专家权重。

该代理只能称为“冻结辅助物理代理”，不得称为 TQH-C2 队列真值估计器。TQH-C2 没有队列、容量、服务量、丢包、往返时延、拥塞窗口或在途字节真值，因此本修复不报告 TQH-C2 状态误差。

## 6. 归一化合同

原始序列与物理序列分别拟合缩放器，但只使用同一批 `2,048` 条开发训练样本。四个窗口共享每个字段的一组统计，禁止逐窗口或逐样本拟合。

连续字段变换固定为：

```text
非负量: log1p(x)
有符号残差: sign(x) * log1p(abs(x))
z = clip((transformed_x - train_median) / train_iqr, -8, 8)
```

- `train_iqr < 1e-6` 的字段标记为常量并在所有划分输出零，不从验证集补尺度。
- 缺失位置在变换后填零，缺失掩码保持 `0/1` 且不缩放。
- `window_valid` 不缩放。
- 原始连续量、物理状态、残差和不确定性分别记录字段统计。
- 缩放器记录训练样本顺序摘要、字段顺序、变换类型、中位数、四分位距、常量标志和 SHA-256。
- 验证集不得拟合任何尺度、缺失规则、不确定性尺度或阈值。

物化顺序固定为三条明确分离的数值路径：

1. `proxy_raw_sequence_unscaled [N,4,16]` 保持共同字段原始单位。ns-3 拟合和 TQH-C2 推理都使用这一语义，HistGradientBoosting 代理不读取 TQH 缩放器。
2. `T-H raw_sequence [N,4,18]` 由同一未缩放 TQH 窗口产生，但只用 TQH 开发训练 `2,048` 条拟合原始历史缩放器，随后补两个恒零位。
3. 物理代理先从第一条路径产生共同辅助尺度下的未标准化物理窗口；再只用这些物理窗口的 TQH 开发训练行拟合独立物理缩放器，得到 `T-P/S/R [N,4,18]`。

三条路径的字段顺序、单位、缩放器摘要和逻辑载荷摘要分别登记。禁止为了省步骤让物理代理读取已经为分类器标准化的值，也禁止让 `T-H` 使用 ns-3 物理代理的输入尺度代替其冻结开发训练缩放器。

## 7. 负对照的确定性构造

### 7.1 `T-S` 整段置换

置换单位是完整的 `physics_sequence[i,:,:]`、`physics_valid[i,:]` 和对应不确定性，三者必须一起移动。分层键固定为：

```text
(source_dataset, transport_family, routing_class, split_id)
```

`routing_class` 由上述部署可观测规则派生，当前试点只能是 `tcp_expert` 或 `shared_only`；模式保留 `udp_expert` 枚举仅用于未来独立任务，本轮计数必须为零。每层使用由实验种子和固定命名空间派生的确定性循环错位，要求供体与受体的 `sample_id` 不同。任何层少于两个样本时硬失败，不得回退到标签或 `profile` 分层。

置换保留整段物理序列内部的跨窗口、跨字段关系与总体缺失分布，只破坏样本对应关系。标签不进入置换键或随机数种子。

### 7.2 `T-R` 坐标随机

开发训练和开发验证的随机值都只能来自开发训练池。池分层键为：

```text
(source_dataset, transport_family, routing_class, window_index)
```

随机化必须在未标准化物理量上完成，顺序固定为：

1. 先从同层开发训练池抽取一条完整的 `physics_valid` 与八字段缺失模式。
2. 对目标模式中每个有效且非缺失的位置，按字段和窗口分别从满足 `physics_valid=1` 且该字段 `missing=0` 的同层开发训练未标准化值池独立抽样。
3. 无效或缺失位置保持空值；张量化时再按合同填零。禁止把源表中的缺失占位零当作有效随机值。
4. 对生成的未标准化物理表应用已经冻结的物理缩放器，得到模型读取的 `[4,18]` 序列。
5. 从抽到的未标准化 `state_uncertainty_start/end` 重新计算 `[0,1]` 的 `physics_uncertainty` 和融合门；不得从标准化后的不确定性反推门值。

该过程破坏字段间和时间上的联合关系，同时保持有效观测的一维边际和合法缺失结构。

随机生成器固定为 `numpy.random.Generator(PCG64)`，种子由 `SHA-256("r2-multiwindow-random-v1\0<seed>\0<split>")` 的前 `64` 位确定。物化清单必须记录每层输入池摘要、输出张量摘要和生成命名空间。

## 8. 模型张量与关键类型

### 8.1 数据类型

建议在 `r2_multiwindow_sidecar.py` 定义：

```python
@dataclass(frozen=True)
class MultiWindowDatasetSettings:
    input_summary: ArtifactSpec
    detection_view: ArtifactSpec
    raw_history: ArtifactSpec
    physics_history: ArtifactSpec
    normalization: ArtifactSpec
    artifact_manifest: ArtifactSpec


@dataclass(frozen=True)
class MultiWindowProbeConfig:
    probe_mode: str
    dataset: MultiWindowDatasetSettings
    model: baseline.ModelSettings
    training: baseline.TrainingSettings
    evaluation: baseline.EvaluationSettings
    run: baseline.RunSettings
    storage: ProbeStorageSettings
    tracking: TrackingSettings
    config_path: Path
    project_root: Path


@dataclass(frozen=True)
class CausalWindowSpec:
    starts: tuple[int, int, int, int]
    stops: tuple[int, int, int, None]
    feature_fields: tuple[str, ...]
    schema_version: str


@dataclass(frozen=True)
class RobustSequenceScaler:
    fields: tuple[str, ...]
    transforms: tuple[str, ...]
    medians: tuple[float, ...]
    iqrs: tuple[float, ...]
    constants: tuple[bool, ...]
    clip_value: float


@dataclass(frozen=True)
class MultiWindowSplit:
    name: str
    sample_ids: tuple[str, ...]
    stable_orders: tuple[int, ...]
    texts: tuple[str, ...]
    labels: tuple[int, ...]
    source_datasets: tuple[str, ...]
    transport_families: tuple[str, ...]
    routing_classes: tuple[str, ...]
    sequence_features: np.ndarray      # float32 [N,4,18]
    sequence_valid_mask: np.ndarray    # bool [N,4]
    sequence_fusion_gate: np.ndarray   # float32 [N]


@dataclass(frozen=True)
class MultiWindowVariantInputs:
    variant: str
    train: MultiWindowSplit
    validation: MultiWindowSplit
    binding: Mapping[str, object]


@dataclass(frozen=True)
class PreparedMultiWindowInputs:
    inputs: MultiWindowVariantInputs
    binding: Mapping[str, object]
    binding_sha256: str
```

`MultiWindowSplit` 构造后必须把三个数组设为只读。全部组的样本顺序、文本摘要和标签摘要必须完全一致。

### 8.2 物化接口

```python
def build_causal_packet_history(
    packet_observations: pyarrow.Table,
    selected_samples: pyarrow.Table,
    *,
    spec: CausalWindowSpec,
) -> pyarrow.Table:
    """返回严格按 stable_order、window_index 排列的 10,240 行窗口表。"""


def fit_sequence_scaler(
    train_windows: pyarrow.Table,
    *,
    value_fields: Sequence[str],
    signed_fields: Collection[str],
) -> RobustSequenceScaler:
    """只在开发训练有效且非缺失值上拟合共享四窗统计。"""


def derive_raw_history_sequence(
    windows: pyarrow.Table,
    *,
    scaler: RobustSequenceScaler,
) -> pyarrow.Table:
    """返回八个标准化连续值和八个缺失位。"""


def derive_physics_sequence(
    windows: pyarrow.Table,
    routes: pyarrow.Table,
    *,
    auxiliary_fit: pyarrow.Table,
    auxiliary_calibration: pyarrow.Table,
) -> pyarrow.Table:
    """用四个冻结前缀代理返回未标准化的严格因果物理窗口表。"""


def normalize_sequence(
    sequence: pyarrow.Table,
    *,
    scaler: RobustSequenceScaler,
) -> pyarrow.Table:
    """应用已冻结缩放器，不重新拟合任何统计。"""


def build_variant_inputs(
    raw_history: pyarrow.Table,
    physics_history: pyarrow.Table,
    *,
    variant: str,
    seed: int,
) -> MultiWindowVariantInputs:
    """只构造请求的一个组，不预构造其余四组。"""


def validate_multiwindow_artifact(
    raw_history: pyarrow.Table,
    physics_history: pyarrow.Table,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """返回可写入收据的行数、形状、因果性、连接和摘要检查。"""
```

### 8.3 批张量

训练批固定为：

```text
input_ids: int64 [B,L], L <= 128
attention_mask: int64/bool [B,L]
labels: int64 [B]
sequence_features: float32 [B,4,18]
sequence_valid_mask: bool [B,4]
sequence_fusion_gate: float32 [B]
```

`sequence_fusion_gate` 定义为：

- `T-A`：输入连续值和缺失位全为零，但保留该样本真实的非空前缀 `sequence_valid_mask`，融合门恒为 `0`。这样既避免全掩码注意力产生非有限值，又不让历史长度进入分类表征。
- `T-H`：存在有效窗口时为 `1`。
- `T-P/T-S/T-R`：`clamp(1 - 有效窗口未缩放状态不确定性均值, 0, 1)`。

门值是离线、停止梯度的置信度，不包含标签、路由掩码或验证统计。标准化后的物理序列虽然也含不确定性字段，但模型不得用它重算门值。

## 9. 因果编码器

在 `r2_multiwindow_fusion.py` 定义：

```python
class CausalWindowEncoder(torch.nn.Module):
    def __init__(
        self,
        *,
        input_dimension: int = 18,
        window_count: int = 4,
        model_dimension: int = 128,
        attention_heads: int = 4,
        feedforward_dimension: int = 256,
        layer_count: int = 1,
        dropout: float = 0.1,
    ) -> None: ...

    def forward(
        self,
        sequence: torch.Tensor,       # [B,4,18]
        valid_mask: torch.Tensor,     # [B,4]
    ) -> torch.Tensor:                # [B,128]
        ...
```

固定内部结构如下：

1. `Linear(18,128,bias=True)` 输入适配。
2. 可学习位置向量 `[1,4,128]`，顺序为最早到最晚。
3. 一层 `TransformerEncoderLayer`：`d_model=128`、`nhead=4`、`dim_feedforward=256`、`dropout=0.1`、`activation="gelu"`、`batch_first=True`、`norm_first=True`。
4. 严格上三角注意力掩码，位置 `i` 不得关注 `j>i`。
5. 无效窗作为键填充掩码；物化器必须保证有效掩码是非空前缀。
6. 取最后一个有效窗口的编码，经 `LayerNorm(128)` 得到 `[B,128]`。

五组都实例化该结构。`T-A` 仍使用同一结构和同一参数量，但输入全零且融合门关闭。按上述模块计算，辅助分支固定包含 `233,985` 个可训练参数，包括输入层、位置向量、单层编码器、末层归一化、`128 -> 768` 投影和一个零初始化标量；实现必须在运行时重新计算并断言该数量，不能只相信文档常量。

## 10. 零初始化有界残差融合

### 10.1 接口

```python
@dataclass(frozen=True)
class FusionDiagnostics:
    raw_alpha: torch.Tensor
    bounded_alpha: torch.Tensor
    encoded_norm: torch.Tensor
    projected_norm: torch.Tensor
    perturbation_norm: torch.Tensor
    relative_perturbation: torch.Tensor
    active_gate: torch.Tensor


class BoundedResidualFusion(torch.nn.Module):
    def __init__(
        self,
        *,
        encoded_dimension: int = 128,
        hidden_dimension: int = 768,
        maximum_relative_norm: float = 0.10,
        epsilon: float = 1e-6,
    ) -> None: ...

    def forward(
        self,
        hidden_state: torch.Tensor,   # [B,768]
        encoded_state: torch.Tensor,  # [B,128]
        fusion_gate: torch.Tensor,    # [B]
    ) -> tuple[torch.Tensor, FusionDiagnostics]:
        ...
```

### 10.2 固定公式

令 `h` 为 DistilBERT 的 `pre_classifier + ReLU` 表征，`z` 为窗口编码，`r=Wz`，则：

```text
base_norm = max(||stopgrad(h)||_2, epsilon)
raw_norm  = max(||stopgrad(r)||_2, epsilon)
norm_scale = min(1, base_norm / raw_norm)
alpha = 0.10 * tanh(alpha_raw)
delta = fusion_gate * alpha * norm_scale * r
h_fused = h + delta
```

约束如下：

- `alpha_raw` 是唯一零初始化参数；`W` 使用固定种子下的标准非零初始化。
- 不得同时把 `alpha_raw` 和 `W` 初始化为零，否则两者乘积会使分支在起始点无梯度。
- 优化第零步 `alpha=0`，因此五组的融合输出都与纯文本表征精确相等。
- 对每个样本都保证 `||delta||_2 <= 0.10 * fusion_gate * ||h||_2`。
- 范数缩放使用停止梯度的范数，防止模型通过操纵分母规避上界。
- `0.10` 是本次唯一修复预注册常量，不按验证结果搜索或改动。
- 融合后直接进入原 DistilBERT `dropout + classifier`，不得再加会破坏初始恒等映射的新归一化层。

每个训练日志至少记录 `alpha_raw`、`alpha`、有效门均值、编码范数、投影范数、扰动范数和相对扰动的均值、50%/95% 分位数及最大值。若实测相对扰动超过 `0.100001`，当前组立即失败。

## 11. DistilBERT 运行接口

v1 模型前向接口固定为：

```python
def forward(
    self,
    *,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    sequence_features: torch.Tensor,
    sequence_valid_mask: torch.Tensor,
    sequence_fusion_gate: torch.Tensor,
    labels: torch.Tensor | None = None,
) -> ProbeModelOutput:
    ...
```

执行接口固定为：

```python
def prepare_multiwindow_probe_inputs(
    config: MultiWindowProbeConfig,
    variant: str,
) -> PreparedMultiWindowInputs:
    """加载并构造且仅构造一个组。"""


def execute_multiwindow_variant(
    config: MultiWindowProbeConfig,
    prepared_inputs: PreparedMultiWindowInputs,
    variant: str,
) -> Mapping[str, object]:
    """执行单个种子、单个组并完成其收尾。"""


def write_seed_summary_if_complete(
    config: MultiWindowProbeConfig,
) -> Mapping[str, object] | None:
    """只有五组绑定均有效且 finished 时写种子汇总。"""
```

命令行固定为：

```bash
uv run python -m flow_probe.r2_distilbert_sidecar_probe \
  --config configs/r2_distilbert_multiwindow_seed42.yaml \
  --variant T-P
```

v1 配置下 `--variant` 必填，只允许 `T-A|T-H|T-P|T-S|T-R`。进程不得在完成一个组后循环到第二组，也不得在同一进程创建第二个 SwanLab 运行。组完成后只允许执行无模型、无 SwanLab 的 `write_seed_summary_if_complete`。

训练合同继续冻结为：批量 `16/64`、梯度累积 `2`、学习率 `2e-5`、权重衰减 `0.01`、`3` 轮、预热比例 `0.1`、最大梯度范数 `1.0`、每 `20` 步保存、总优化步 `192`、种子 `42/43/44`。本修复禁止调整学习率、样本比例、轮数、旁路维度、残差上界、种子或验证划分。

每个种子在五个独立进程中必须具有相同的 DistilBERT 头、窗口编码器、投影和 `alpha_raw` 初始化摘要。数据加载顺序也由同一训练种子生成。若同种子五组初始化摘要不同，全部五组作废。

负对照只能使用独立的 NumPy `PCG64` 实例，不得消耗 Python 全局、NumPy 全局或 PyTorch 随机状态。每个进程在构造模型前重新设置固定训练种子；数据准备或组名分支不得改变模型初始化所见的 PyTorch 随机状态。

## 12. 启动器与输出布局

新输出根固定为：

```text
runs/r2-transformer-sidecar-probe/distilbert-multiwindow-v1/
  seed-42/{t-a,t-h,t-p,t-s,t-r}/
  seed-43/{t-a,t-h,t-p,t-s,t-r}/
  seed-44/{t-a,t-h,t-p,t-s,t-r}/
```

启动器顺序固定为：

```text
42: T-A -> T-H -> T-P -> T-S -> T-R
43: T-A -> T-H -> T-P -> T-S -> T-R
44: T-A -> T-H -> T-P -> T-S -> T-R
```

每次只执行一个 `uv run ... --variant ...`。启动器必须用 `PIPESTATUS[0]` 记录 Python 真实退出码；当前组非零退出时保留日志和状态并停止，不在循环内自动重试。显式重新启动脚本时，可按绑定和状态恢复。

每组拥有独立：

- `run-state.json`
- `run-binding.json`
- `console.log`
- `swanlab_metrics.jsonl`
- 检查点目录
- 最佳模型目录
- 指标、预测、收尾收据和制品清单

只有一个种子的五组全部 `finished` 且收据有效时才写该种子汇总。只有十五组全部有效时才允许运行离线裁决。

## 13. 恢复与检查点边界

### 13.1 运行绑定

v1 绑定至少包含：

- 三个新配置的字节摘要与解析快照。
- 检测视图、原始历史、物理历史、缩放器、输入摘要和制品清单 SHA-256。
- 包表、协议表、原 `observation_sequence_sha256` 集合摘要。
- 窗口边界、字段顺序、归一化公式、路由合同和物理前缀模型摘要。
- 负对照分层键、随机命名空间和请求组。
- `seed`、`variant`、样本顺序、文本、标签和张量摘要。
- 因果注意力掩码公式、编码器规格、辅助参数量、初始化摘要、零初始化状态和 `0.10` 上界。
- 所有语义依赖源码的 SHA-256。
- `final_test_visible=false`。

任一项不一致都必须拒绝恢复，不能静默重算并写入原目录。

### 13.2 检查点内容

每 `20` 个优化步以内保存：

- DistilBERT 全部参数。
- `CausalWindowEncoder`、`128 -> 768` 投影和 `alpha_raw`。
- 优化器、调度器、混合精度缩放器。
- Python、NumPy、CPU 与全部 CUDA 随机状态。
- 当前轮次、下一批索引、全局步、最佳轮次和最佳指标。
- 运行绑定摘要、参数合同、初始化摘要和融合规格。

最佳模型包保存 DistilBERT 标准制品、`multiwindow_fusion.pt` 和 `multiwindow_fusion_config.json`。加载时使用严格键匹配；缺一项即拒绝。

### 13.3 状态恢复

- `finished`：校验收尾收据、最佳模型收据和制品清单后跳过。
- `finalizing`：按既有幂等收尾协议继续，不重新训练。
- `prepared/running/interrupted`：只从同绑定的最新合法检查点恢复。
- `failed` 且存在同绑定合法检查点：用户显式重启启动器后允许恢复，保留旧失败尝试。
- `failed` 且失败阶段为 `tracking_init`、全局步为零：显式重启后可在同组目录创建下一尝试，不需要伪造检查点。
- 已训练但无合法检查点：拒绝续跑，不从不完整模型猜测状态。
- 绑定不一致、收据损坏或制品摘要不一致：拒绝覆盖；必须使用新的输出目录并保留旧证据。

运行状态建议新增 `failure_stage` 和仅追加的 `attempts` 列表，使 SwanLab 初始化失败、训练失败和收尾失败可区分。

## 14. SwanLab 边界

正式训练继续固定使用项目 `mortiswang/malicious-traffic-llm`，在线模式是正式运行门禁。一个变体进程对应一个 SwanLab 运行和一个本地尝试。

顺序固定为：

1. 校验配置、输入摘要、张量形状、因果性、路由、磁盘、CUDA、模型结构和运行绑定。
2. 先把 `{attempt, status: initializing, started_at}` 原子写入本地状态。
3. 再执行 `swanlab.init`。
4. 成功后立即补写工作区、项目、运行标识和运行网址，再开始训练。
5. 失败时把异常阶段和消息写入该尝试，结束当前进程，不自动创建第二次在线会话。

因此，SwanLab `401` 或网络初始化失败不会丢失本地证据，也不会污染训练步；用户显式重启后创建新的尝试。训练中 SwanLab 失败不得删除合法检查点。`swanlab_metrics.jsonl` 按尝试追加，每行必须包含 `attempt`、`variant`、`seed` 和 `global_step`，避免跨尝试步号歧义。

种子汇总和十五组离线分析不得创建 SwanLab 运行。

## 15. 物化制品

新派生根固定为：

```text
runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/
```

至少生成：

| 制品 | 合同 |
| --- | --- |
| `detection-view.parquet` | 与旧 `2,048/512` 样本、顺序、文本来源和标签完全一致 |
| `raw-history.parquet` | `2,560 × 4 = 10,240` 行原始窗口和审计字段 |
| `physics-history.parquet` | `10,240` 行严格因果物理窗口、缺失、不确定性和只读路由审计 |
| `normalization.json` | 仅开发训练拟合的原始与物理缩放器 |
| `input-summary.json` | 计数、模式、路由、短流、跨域和禁止字段摘要 |
| `artifact-manifest.json` | 全部非自指制品的字节数和 SHA-256 |

`raw-history.parquet` 和 `physics-history.parquet` 按 `stable_order,window_index` 唯一排序。模型读取投影不得包含 `binary_label` 之外的训练目标，也不得包含 `profile`、来源路径、场景、采集单元、协议路由掩码或 QUIC 线图像字段。标签只由检测视图单独加载并在 `sample_id` 一一连接后用于分类损失。

物化必须是确定性的；同一配置、源码和输入重新物化后，规范化逻辑内容摘要必须一致。由于 Parquet 元数据可能受库版本影响，门禁同时记录字节 SHA-256、模式摘要和按稳定顺序计算的逻辑载荷摘要。

## 16. 正式入口必须断言的门禁

在加载 GPU 模型前完成以下检查：

1. 样本精确为开发训练 `2,048` 和开发验证 `512`，无额外划分。
2. `final_test_visible=false`，所有输入路径不含最终测试标记。
3. `sample_id` 唯一且原始/物理/检测视图一一对应。
4. 包行精确关联 `173,196`，复合包键不重复。
5. 四窗边界、`packet_index` 顺序和非负累积时钟符合合同。
6. 有效窗是非空前缀，短流未删除，连续值和缺失位有限且一致。
7. 原始与物理张量都精确为 `[N,4,18]`，最后两个保留位全零。
8. 物理窗口 `t` 的依赖摘要只包含原始窗口 `0..t`。
9. `92` 条 UDP 承载未知样本全部 `shared_only`，`udp_expert_mask=0`，QUIC 专家全关闭。
10. 归一化统计只绑定开发训练；随机旁路池只绑定开发训练。
11. 五组样本、文本、标签、模型结构、参数量和训练预算一致。
12. 同种子各组初始化摘要一致，`alpha_raw=0`。
13. 模型前向第零步满足 `h_fused == h`，数值误差不超过当前数据类型允许范围。
14. 运行绑定、语义依赖和所有输入制品摘要匹配。
15. SwanLab 标签长度和固定工作区/项目满足合同。

任一门禁失败都只终止新 v1 当前组，不得停止、清理或修改正在运行的 v0 实验。

## 17. 裁决语义

旧 v0 `T-A` 不能替代新 v1 `T-A`，旧 `T-P/S/R` 也不能与新多窗口组混算。十五组必须全部重跑并按种子完整报告。

每个种子至少比较：

```text
P - A  物理序列相对纯文本
P - H  物理变换相对等信息原始历史
P - S  正确配对相对整段错配
P - R  真实结构相对坐标随机
```

只有 `T-P` 在全部预注册种子上相对 `T-A/T-H/T-S/T-R` 形成一致、配对且统计支持的开发增益，才允许进入完整 R2/Qwen。若 `T-H` 提升而 `T-P` 不超过 `T-H`，结论只能是历史信息有效，不能归因于物理建模。若 `T-P` 仍不超过负对照，停止当前 R2 检测增益路径，不调整学习率、不挑种子、不改变样本比例，也不进行第二次结构补救。

本轮不使用最终测试。最终测试只可在后续独立、已通过方法选择门禁的最终评估阶段按既定规则一次性使用。

## 18. 实现验收接口摘要

实现代理必须按本规格提供并绑定下列关键接口：

```text
build_causal_packet_history(...) -> pyarrow.Table
fit_sequence_scaler(...) -> RobustSequenceScaler
derive_raw_history_sequence(...) -> pyarrow.Table
derive_physics_sequence(...) -> pyarrow.Table
normalize_sequence(...) -> pyarrow.Table
build_variant_inputs(..., variant, seed) -> MultiWindowVariantInputs
validate_multiwindow_artifact(...) -> dict[str, object]

CausalWindowEncoder.forward([B,4,18], [B,4]) -> [B,128]
BoundedResidualFusion.forward([B,768], [B,128], [B])
  -> ([B,768], FusionDiagnostics)

prepare_multiwindow_probe_inputs(config, variant) -> PreparedMultiWindowInputs
execute_multiwindow_variant(config, prepared_inputs, variant)
  -> Mapping[str, object]
write_seed_summary_if_complete(config) -> Mapping[str, object] | None
```

任何实现若改为无界相加、允许一个进程执行多个组、把路由掩码拼入分类表示、让较早物理窗口读取较晚窗口、让验证集参与归一化或随机池、沿用未知 UDP 的 UDP 专家，均不符合本规格。
