# FT C00 双选轮本机筛选任务计划

- **状态**：实施准备
- **目标**：用同一 Python 工具在本机 MPS/FP32 和服务器 CUDA/BF16 上训练裸 FT C00，并从同一训练轨迹保存逐流 AP 与实体 AP 两份最优检查点。
- **证据等级**：本机为 `screening_only`；服务器完整预算才可进入正式证据。

## 阶段

- [x] 核验本机硬件、MPS、LSPR23 缓存与依赖。
- [x] 核验现有 FT 数值分词、模型结构、选轮和检查点接口。
- [x] 生成并核验本机 LSPR23 训练区字段基数收据。
- [x] 完成实现计划；统一运行合同由独立文档代理收尾。
- [ ] 实现单代码双运行配置与真实数据校准入口。
- [x] 在本机执行真实单步吞吐/内存校准并冻结筛选预算。
- [ ] 运行 C00 双选轮筛选并回收完整制品。
- [ ] 根据源年结果裁决后续候选的统一选轮协议。

## 硬边界

1. 只读 LSPR23；LSPR24 读取计数为零。
2. C00 是裸 FT：不得经过旧 CPA 的零上下文融合层或携带 `p_log`。
3. 同一次训练、同一模型状态、同一验证前向同时计算逐流 AP 与实体 AP。
4. MPS 检查点不得续训为正式 CUDA 模型；只复用代码和模式。
5. 本机预算由真实吞吐收据推导，不凭空填写轮数或步数。
6. 不创建人工测试或合成性能结论；静态入口后直接运行真实 LSPR23 校准。

## 文件所有权

- 新建 `thesis/experiments/llm_probe/tools/ch3_ft_c00_dual_selection.py`
- 新建 `thesis/experiments/llm_probe/configs/ch3-ft-c00-dual-selection-mps-screening-v1.json`
- 新建 `thesis/experiments/llm_probe/configs/ch3-ft-c00-dual-selection-cuda-formal-v1.json`
- 新建 `thesis/experiments/llm_probe/scripts/local_launchers/run_ch3_ft_c00_dual_selection_mps_screening_v1.sh`
- 新建 `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_ft_c00_dual_selection_cuda_formal_v1.sh`
- 本目录 `notes.md`、`implementation-plan.md` 与后续实施报告

不修改现有 FT 工具、配置、启动器、运行根或历史检查点。
