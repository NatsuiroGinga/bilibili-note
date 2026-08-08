# E2 DistilBERT 正式启动器报告

## 范围

本任务只新增 E2 普通 DistilBERT 的正式运行驱动、持久化 Shell 启动器和最小合同测试，不修改数据加载、模型训练、评价指标或其他实验入口。

## 新增文件

- `thesis/experiments/llm_probe/scripts/e2_distilbert_formal_driver.py`
- `thesis/experiments/llm_probe/scripts/run_e2_distilbert_formal.sh`
- `thesis/experiments/llm_probe/tests/test_run_e2_distilbert_formal_wrapper.py`

## 冻结行为

- 数据：TQH-C2 v1.2.0 冻结开发协议视图。
- 面板：`A+B+D→C`。
- 输入：由 `E2_FEATURE_FIELDS` 给出的七个共同字段。
- 模型：`/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased`。
- 种子：`42`。
- 阈值：只在源域校准集选择。
- 设备：CUDA；精度由现有运行时安全选择。
- 跟踪：`mortiswang/malicious-traffic-llm` 在线模式，开始和结束均写数值指标，避免云端运行只有日志而没有图表。

## 持久化证据

启动器为每次运行创建唯一输出目录和启动证据目录，保存配置快照、代码与输入哈希、模型绑定、能力清单、控制台日志、SwanLab 本地日志、运行状态、训练摘要、逐样本预测、统一指标、最终模型检查点和输出哈希。

当前 E2 训练适配器不暴露优化器、调度器和随机状态，因此正式入口不会伪装成支持断点续训。服务器中断后执行 `recover` 会写入 `interrupted_no_resumable_checkpoint`，保留旧制品并要求使用新运行身份重跑。

## 启动命令

同步并核对脚本 SHA-256 后，在服务器项目根执行：

```bash
bash scripts/run_e2_distilbert_formal.sh formal <基础模型绑定SHA-256>
```

服务器重启后检查旧运行：

```bash
bash scripts/run_e2_distilbert_formal.sh recover <启动证据目录>
```

## 验证

- 只执行 Python 语法编译检查和 Shell `bash -n`。
- 按任务边界未在本机运行 `pytest`、格式化、SSH、`rsync` 或正式实验。
