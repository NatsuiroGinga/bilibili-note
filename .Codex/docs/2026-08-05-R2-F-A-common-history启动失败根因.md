# R2 F-A `common-history` 启动失败根因调查

- 调查日期：2026-08-05
- 范围：仅调查 PINN/R2 的 F-A 启动前数据制品门禁失败；未修改生产文件，未同步制品，未启动或重启实验。
- 异常：`r2_final_views.py` 报告 `公共历史不是普通文件`，目标为 `runs/data-prepared/r2-final-sidecar-candidate-v1/common-history.parquet`。

## 调查方法

按根因调查顺序，先定位异常断言，再核对调用配置、本地源制品、服务器实际输入集合和迁移链路。未提出或执行修复。

`r2_final_views.py` 的 `_verify_artifact` 会先解析路径，并在路径不是普通文件或仍为符号链接时抛出该异常；只有通过该检查后才计算 SHA-256。因此该错误发生在 Parquet 读取和哈希核验之前。

## 证据

### 1. F-A 配置的精确期望

`configs/r2_final_distilbert_f-a_seed42.yaml` 将训练划分共同历史固定为：

- 路径：`runs/data-prepared/r2-final-sidecar-candidate-v1/common-history.parquet`
- SHA-256：`e8f8b83b1eabc6d649b67feb845e5b04e233522c3815e167d0ea6e909beb35f6`

同一份配置还要求训练划分路由文件：

- 路径：`runs/data-prepared/r2-final-sidecar-candidate-v1/route-assignments.parquet`
- SHA-256：`b46a08006c16ea669ddc642651ead49ffe6bd8193dec06ebcaba186bcf68a461`

角色清单要求三份共同历史均为 `deployment_observable_causal_history`，且 F-A 入口在读取任何 Parquet 前逐一验证共同历史、检测视图和路由视图。

### 2. 本机源制品正确且不是符号链接

本机 `common-history.parquet` 的 `stat` 结果为普通文件，模式 `-rw-r--r--`，大小 `629,766` 字节，链接计数为 `1`；本机计算的 SHA-256 与配置期望一致。

候选根的 `artifact-manifest.json` 同时登记该文件为 `30,316` 行、`629,766` 字节和相同 SHA-256。

控制器对另一缺失文件的本机核验显示，`route-assignments.parquet` 大小为 `292,868` 字节，SHA-256 为配置登记的 `b46a08006c16ea669ddc642651ead49ffe6bd8193dec06ebcaba186bcf68a461`。

因此，本机源不存在符号链接，也不存在需要额外迁移的链接目标。

### 3. 新服务器的实际输入集合

控制器在当前 `378` 服务器的同一 F-A 输入清单上完成只读核验：13 个被 F-A 引用的制品中，11 个存在且哈希匹配；仅以下两个训练划分派生制品缺失：

- `runs/data-prepared/r2-final-sidecar-candidate-v1/common-history.parquet`
- `runs/data-prepared/r2-final-sidecar-candidate-v1/route-assignments.parquet`

服务器的 `r2-final-sidecar-candidate-v1` 候选目录本身存在。这排除项目根、候选目录整体缺失、配置版本不匹配和其他 11 个输入整体迁移失败。

本调查代理对服务器执行独立只读 `stat` 时，连接被本机代理关闭并返回 `255`；依据服务器恢复规则未自动重试。该连接失败不改变控制器已取得的同服务器制品核验事实。

## 单一根因假设

**新服务器迁移或白名单同步遗漏了训练划分的两个候选派生制品，导致 F-A 所需的 `common-history.parquet` 在配置规定路径不存在。**

该假设解释全部已知现象：

- `_verify_artifact` 在哈希检查前将缺失路径判为“不是普通文件”。
- 两个缺失项都位于同一候选根，且都属于训练划分；校准、开发验证和其余 11 个输入已成功到位。
- 本机两项制品均为普通文件并且哈希与冻结配置一致，排除本机生成错误、符号链接或链接目标遗漏。

当前没有证据支持“服务器将普通文件错误变为目录”或“符号链接目标未迁移”这两种替代解释。若补同步后仍失败，才应以服务器 `stat` 的具体类型结果为新证据重新调查。

## 最小解锁动作

仅将以下两份本机普通文件同步到服务器的**同名原路径**，不删除或覆盖任何其他制品：

- `runs/data-prepared/r2-final-sidecar-candidate-v1/common-history.parquet`
- `runs/data-prepared/r2-final-sidecar-candidate-v1/route-assignments.parquet`

同步完成后，在服务器只读验证两项均为非符号链接的普通文件，并逐项核对 SHA-256 为：

- `common-history.parquet`：`e8f8b83b1eabc6d649b67feb845e5b04e233522c3815e167d0ea6e909beb35f6`
- `route-assignments.parquet`：`b46a08006c16ea669ddc642651ead49ffe6bd8193dec06ebcaba186bcf68a461`

两项验证通过后，才由既有统一启动器重新执行 F-A 启动门禁；本调查不执行该操作。

## 未变更内容

- 未修改 R2 代码、配置、清单或恢复文档。
- 未启动 GPU 训练、物理拟合、视图物化或 F-A 运行。
- 未执行删除、覆盖或服务器同步。
