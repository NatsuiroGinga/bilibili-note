# QUIC-MedNetCom 下载固定计划

## 目标

从官方公开仓库取得 QUIC-MedNetCom，固定到提交 `f237a20360b83868a197488c5b557f53e4b7e53c`，并生成可复核的来源、文件统计、逐文件 SHA-256 和 qlog 解析证据。

## 边界

- 只下载 QUIC-MedNetCom，不下载 H23Q。
- 原始数据唯一落盘位置为 `raw/datasets/QUIC-MedNetCom/`。
- 不修改原始内容，不进行正式物化，不连接 GPU 服务器。
- 不运行格式化、Pyright、pytest、Prettier 或无关 Git 检查。
- 许可不明确时只能内部实验使用，禁止公开再分发原始数据。

## 阶段

- [x] 阶段一：读取根规则、原始材料规则、过程文档规则和实验数据规则。
- [x] 阶段二：检查本机重复副本、目标目录和磁盘空间。
- [x] 阶段三：从官方仓库下载并固定指定提交。
- [x] 阶段四：核验提交、文件数、qlog 数量、总字节数和 qlog 可解析性。
- [x] 阶段五：生成逐文件 SHA-256 清单、来源记录和最终回执。

## 验收制品

- 原始数据：`raw/datasets/QUIC-MedNetCom/`
- 逐文件清单：`raw/datasets/QUIC-MedNetCom/SHA256SUMS.codex.txt`
- 来源记录：`raw/datasets/QUIC-MedNetCom/SOURCE.codex.md`
- 过程笔记：`.Codex/docs/2026-08-03-QUIC-MedNetCom下载固定/notes.md`
- 最终回执：`.Codex/docs/2026-08-03-QUIC-MedNetCom下载固定/report.md`

## 决策

- `raw/AGENTS.md` 明确大体量正式数据按实验项目清单管理，但现有工程 `data/README.md` 又明确原始数据来自仓库 `raw/datasets/`；因此只在 `raw/datasets/QUIC-MedNetCom/` 保存一份原件，并由后续实验清单引用。
- qlog 解析检查只做 JSON/JSON-SEQ 语法与基本结构审计，不对原始文件重写或标准化。

## 错误记录

- 首次创建文档时父目录不存在，随后创建专用目录后重试；未影响数据文件。

## 状态

任务完成。数据已固定并通过完整性检查，可以进入 QUIC 物理字段与单位审计。
