# 正式 TCP/UDP PINN 专家运行报告

## 当前结论

- 状态：`finished`。种子 42 正式 TCP/普通 UDP PINN 专家已使用 v3 物理池完成 `300` 个优化步，检查点、指标、绑定收据和启动日志已回收到本地。
- 结果：正式拟合耗时 `20.6845` 秒，验证集路由专家总损失为 `0.620644`；固定残差零坍缩、TCP/UDP 动力学、等容量和不可变检查点绑定门禁全部通过。
- 边界：不读取最终测试集，不改变 TQH 数据、划分、评价协议或 E2 基线，不启用 QUIC 专家，不向 SwanLab 上传。
- 生产代码：无需修改；复用既有正式拟合入口和冻结模型实现。
- 结论边界：本次只证明 v3 TCP/UDP 物理专家可复现拟合并通过物理门禁，不证明 E2 检测收益或 PINN 方法优于基线。

## 执行计划

- [x] 恢复 PINN/R2 路线规则并完成服务器只读就绪核对。
- [x] 核对 v3 物理池与 E2 七字段辅助表绑定。
- [x] 新增并验证 v3 角色清单与种子 42 本地记录配置。
- [x] 同步白名单配置并启动一次正式拟合。
- [x] 回收检查点、指标、日志、状态和制品清单，完成结果核验。

## 就绪证据

- 服务器 GPU：单卡 NVIDIA GeForce RTX 5090，显存 32607 MiB；核对时使用量为 0 MiB，利用率 0%。
- 磁盘：`/root/autodl-tmp` 共 100 GiB，已用 61 GiB，可用 40 GiB。
- 运行冲突：核对时没有 E2 DistilBERT、E2 A/S/P/X 或 PINN 拟合活动进程，且没有活动 `screen` 会话。
- v3 物理池：`46080` 个窗口、`11520` 个序列，`384` 个开发运行纳入，`128` 个测试或未见配置运行未物化；`final_test_visible=false`。
- v3 主表 SHA-256：`a4780ccfe92f9b391261bf918cb6d524a2b741e3bf384c91bc2215c25d672c2a`。
- v3 载荷 Merkle SHA-256：`f3591ae90c5789b6a0f8345280bed08c63017021f237c7e41d53a586098d03ac`。
- E2 辅助表：`46080` 行，源表 SHA-256 与 v3 主表一致；绑定 SHA-256 为 `c3ff0b2219378c91d33a9255b3e284e7cd6e0ce8c5dbdd016494f99465d011f7`。
- 既有同规模种子 42 正式拟合耗时为 `25.40` 至 `27.06` 秒；本轮预计训练 `30` 至 `60` 秒，连同启动门禁与收据核验不超过 `2` 分钟。
- 活跃比较支路共 `495042` 个可训练参数；预计峰值显存低于 `1` GiB，按 `1` 至 `2` GiB 保守预留。

## 配置与实现绑定

- 拟合配置：`thesis/experiments/llm_probe/configs/r2_final_physics_fit_seed42_tcp_udp_v3_formal.yaml`，SHA-256 为 `f86578b26c88afdcaee67b6745601024168da60533673d906ac7076f426fa590`。
- 角色清单：`thesis/experiments/llm_probe/configs/r2_final_physics_role_manifest_v3.json`，SHA-256 为 `175fad75249b63ba2ec47ed7431a817a6c7b8b5c066dba32f9a5017b49117e9d`。
- 配置语义摘要：`1a0eed16a39e35f3c877c8d18168380cfbac7fd105dcee656502e1a6598151a8`。
- 专家实现 SHA-256：`3b1d53da100cb5d9a02f504da69dd9976c720af2cbfe68fe3b14e23c610f8465`。
- 拟合实现 SHA-256：`0e509825bf79bb8c3d10296cf0b56828882a53dcf49f7bd1d614f355f196a2fb`。
- 正式包装器 SHA-256：`0911531f64ad33f24525b344f11091a8ae6c522324ca9eb4089b19f1c19bf22e`。
- 跟踪模式固定为 `local`；输出目录没有 SwanLab 文件或运行地址。

## 运行身份

- 服务器输出根：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/r2-final-physics-fit/tcp-udp-v3-seed-42-formal`。
- 本地回收根：`thesis/experiments/llm_probe/runs/r2-final-physics-fit/tcp-udp-v3-seed-42-formal`。
- 服务器启动器：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/launchers/r2-final-physics-fit/r2_final_physics_fit_seed42_tcp_udp_v3_formal-20260807T053630Z`。
- 本地启动器副本：`thesis/experiments/llm_probe/runs/launchers/r2-final-physics-fit/r2_final_physics_fit_seed42_tcp_udp_v3_formal-20260807T053630Z`。
- 启动会话：`r2-pinn-v3-s42`；完成后会话与主进程均已退出，GPU 回到 `0 MiB`、利用率 `0%`。
- 显存测量限制：启动后 3 秒采样为 `3 MiB`、完成后为 `0 MiB`；任务仅运行 `20.6845` 秒，在第二次采样前已结束，因此没有可信峰值显存收据，不能把预估的 `1` 至 `2` GiB 当作实测峰值。

## 拟合结果

- 开发划分序列数：训练拟合 `7680`，校准 `1920`，验证 `1920`。
- 训练预算：`10` 轮、`300` 个优化步；`metrics.jsonl` 共 `310` 行，即 `300` 条优化步和 `10` 条校准记录。
- 三个比较支路的活跃参数量均为 `165014`；等容量收据为真。完整路由系统为 `219607` 个参数，其中 `54593` 个 QUIC 参数属于休眠排除项。

| 验证指标 | 路由专家 | 统一控制 | 历史控制 |
| --- | ---: | ---: | ---: |
| 总损失 | 0.620644 | 0.617783 | 0.619319 |
| 共享守恒状态损失 | 0.0274103 | 0.0277273 | 0.0271952 |
| 共享守恒残差损失 | 6.60383e-06 | 4.06658e-06 | 4.34336e-05 |
| TCP 状态损失 | 0.540694 | 0.540835 | 0.540576 |
| TCP 残差损失 | 0.000595010 | 0.000327812 | 0.000819359 |
| UDP 状态损失 | 0.0524791 | 0.0491865 | 0.0515474 |
| UDP 残差损失 | 5.43638e-06 | 1.30289e-05 | 1.03414e-05 |

## 物理门禁

- `formal_tcp_udp_dynamics_ready=true`，阻塞原因为空。
- 共享守恒、TCP、UDP 专家的固定残差算子可训练参数均为 `0`，预测状态梯度均非零。
- TCP 慢启动、拥塞避免、丢包和超时四个方程均有非平凡残差和非零预测状态梯度；关键终点梯度非零。
- UDP 应用发送守恒残差为非平凡构造，预测状态梯度 L2 为 `3.46411`。
- `quic_expert_ready_after_fit=false`；QUIC 专家没有被标记为正式就绪。

## 制品清单

下表 SHA-256 已在服务器计算，并在本地回收后逐项复算一致。

| 相对路径 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `checkpoint-latest.pt` | 6228176 | `39e925e393ab35ee5a6801922b891c4d65b8826ab4aa3dde86351f0d690d4231` |
| `checkpoint-binding-manifest.json` | 2385 | `9342dbcbcb3449a80f7531cdc8aabd10864b977f4cbde6770bceccdbba2a531f` |
| `zero-collapse-receipt.json` | 2889 | `8e41f2d164115b55adbcba1087f43e10379bcedd650c454402df5689c6e7e0e0` |
| `run-binding.json` | 5860 | `5bbd6da71be686f0a4ec8f48eee8d05f2413b946a20c8b53bd39d8cc644c5f1e` |
| `result.json` | 7790 | `78a0838e8d149f14e6cfa972f28316ff42f806fb0b3f5197d51be73a12fdb76d` |
| `metrics.jsonl` | 425163 | `5ec5085677a6dabb76f0eb6b9647a032817c246f8b8324c4507a9a1203a23b9a` |
| `launcher.log` | 7790 | `78a0838e8d149f14e6cfa972f28316ff42f806fb0b3f5197d51be73a12fdb76d` |
| `status.txt` | 9 | `161069badc0cc23058b13d7c068e45205f4333aa15fd78db9d68f5c9f1ae8983` |

不可变检查点清单中的检查点 SHA-256 与实际文件一致，状态为 `frozen`，并绑定种子 `42`、v3 输入 Merkle、配置 SHA-256 和冻结实现摘要。

## 验证情况

- 本地与远端配置 SHA-256 完全一致，远端 `--validate-config-only` 返回 `config-valid`。
- 远端启动器状态为 `finished`，日志非空；本地回收的 `launcher.log` 与 `result.json` 逐字节一致。
- 本地使用 `jq -e` 核对完成状态、步数、种子、v3 输入绑定、配置绑定、等容量、零坍缩和 QUIC 禁用，全部通过。
- 本地核对指标日志行数为 `310`，检查点 SHA-256 与不可变清单一致。
- 没有运行完整测试、格式化或非阻断复审；本轮没有修改 Python 或 Shell 生产代码，按项目规则只执行配置与制品精确门禁。

## 风险与门禁

- v3 物理池状态为 `review_pending`，但完整物化、原子发布、来源哈希、方向字段和最终测试隔离均已通过；按项目规则，非阻断复审不延迟已满足门禁的实验。
- 现有种子 42 配置绑定旧 v2 物理池并使用 SwanLab 在线模式，不能原样复用；本轮只新增 v3 配置和角色清单。
- QUIC 正式专家仍未就绪；本次检查点不得被解释为包含可用 QUIC 专家。
- 单种子物理拟合指标不是检测性能，也不能替代 E2 A/S/P/X 因果比较或正式多种子统计。

## 错误记录

- 首次远程只读命令受本机沙箱网络限制，非服务器故障；获批使用既有统一入口后服务器核对成功。
- 服务器没有 `fd` 命令，但存在 `/usr/bin/fdfind`；后续文件枚举使用 `fdfind`。
- 首次白名单同步请求被自动审批拒绝，原因是尚未明确授权把两个具体配置文件发送到指定远端目录；没有采用其他传输方式绕过审批，获得用户精确授权后由主代理完成同步。
- 首个远端聚合验收命令因 `jq` 程序中的 `$input` 被 Shell 提前展开而退出；该命令只读且未修改制品。随后改用分开的原始 JSON、SHA-256 和进程状态读取，并在本地完成断言，全部通过。

## 变更范围

- 新增 `thesis/experiments/llm_probe/configs/r2_final_physics_fit_seed42_tcp_udp_v3_formal.yaml`。
- 新增 `thesis/experiments/llm_probe/configs/r2_final_physics_role_manifest_v3.json`。
- 新增本报告及本地 `runs/` 回收副本。
- 未修改 `r2_final_physics_fit.py`、`r2_final_experts.py`、任何 E2 A/S/P/X 运行目录、`e2_distilbert.py`、TQH 数据、划分、评价协议或 QUIC 生产代码。
