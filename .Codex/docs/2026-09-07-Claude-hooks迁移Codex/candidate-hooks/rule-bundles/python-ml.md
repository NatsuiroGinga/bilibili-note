【按需注入·Python/ML 代码规范】本条规则因本次触碰 Python/实验文件注入，写此类代码必须遵守。

## 结构与风格
- 小文件原则：每文件 200-400 行，超 400 拆分模块；禁止单文件超 800 行；嵌套不超过 4 层（早返回）
- 配置优先：`@dataclass(frozen=True)` 承载配置，禁止全局变量与硬编码超参（从 cfg 读）
- 函数必须有类型注解；禁止可变默认参数（`def foo(a=None)`）；禁止裸 `except:`，捕获具体异常类型并记录后 raise
- import 顺序：标准库 → 第三方 → 本地模块；类 PascalCase、函数/变量 snake_case、常量 UPPER_SNAKE_CASE
- 模块级 `logger = logging.getLogger(__name__)`；DEBUG=细节 / INFO=进度 / WARNING=可恢复 / ERROR=失败 / CRITICAL=不可恢复；禁止 print 调试
- 每个包 `__init__.py` 定义 `__all__` 显式公开 API

## ML 项目专项
- 所有模块用 Factory & Registry 模式：`register_xxx(name)` 装饰器 + `XXX_FACTORY` 字典 + 工厂函数
- 模型 `__init__` 只接受 cfg 参数，超参全部来自配置（Hydra + OmegaConf）
- 目录：`run/conf`（Hydra 配置）、`run/pipeline`（工作流）、`run/outputs`（输出）、`src/{data_module,model_module,trainer_module,utils}`

## 实验可复现
- 入口处 `set_seed(seed)`：random/numpy/torch/cuda 全设，`PYTHONHASHSEED`，需要确定性时 `cudnn.deterministic=True`
- Hydra 自动保存解析后配置到 `outputs/{experiment}_{timestamp}/`；配置与环境（python/torch/cuda 版本、GPU 型号）随实验日志记录；`pip freeze` 存 outputs 旁
- checkpoint：保存 best（按验证指标）+ last N；dict 含 epoch/model/optimizer/scheduler/best_metric/config
- 数据集记 SHA256 哈希或版本标签到实验日志，预处理步骤写入文档
- 验证清单：mypy + ruff + pytest 通过后才提交
