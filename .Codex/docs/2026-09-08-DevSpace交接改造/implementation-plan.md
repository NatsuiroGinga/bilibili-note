# 通用 ChatGPT 交接 Broker 实施计划

> **供实现代理执行：** 必须逐任务使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`。实现开始前需获得用户对 [设计](design.md) 的明确批准。

**目标：** 将现有只读原型改造为跨项目、句柄驱动、可审计且只允许单次受限 Markdown 回写的 broker，并保留人工回收路径。

**架构：** 本地 CLI 管理项目、脱敏快照、派发、重试、人工回收和查询；远程 MCP 只按 `handoff_id` 取一个不可变出站包，或向其预创建槽提交一次 Markdown。用户级状态库存放路径映射和哈希链收据，客户端不提交路径。

**技术栈：** Python 3.11+、标准库 `sqlite3`/`hashlib`/`secrets`/`pathlib`、Python MCP SDK 1.x、uv、`unittest`、可选 OAuth 2.1/RFC 9728/RFC 8707 适配。

**规格：** `.Codex/docs/2026-09-08-DevSpace交接改造/design.md`

## 全局约束

- 不安装或复用 DevSpace，不引入 shell、exec、补丁、附件、工作树或进程会话。
- 远程工具精确等于 `fetch_handoff` 和 `submit_handoff_result`。
- 客户端参数不得含路径、目录、glob、命令、URL、附件或工作区打开参数。
- 出站、入站默认上限均为 `262144` 字节，硬上限为 `1048576` 字节。
- 状态只允许 `created/dispatched/running/completed/failed/expired`，后三者为终态。
- 相同内容重放返回同一收据；不同内容不得覆盖；修订创建新 `handoff_id`。
- 默认只允许本地 `stdio` 或 `127.0.0.1`；远程 HTTPS/OAuth 默认关闭。
- 收据不记录正文、令牌、绝对路径、IP、完整 User-Agent、仓库远端或自由文本。
- 结果始终标记为“外部候选，待本地全文和实验复核”。
- 手工修改只用 `apply_patch`；Python 不运行 `black`。

## 文件职责

| 文件 | 职责 |
| --- | --- |
| `tools/chatgpt_handoff.py` | 本地 init/register/create/dispatch/status/retry/receive/collect |
| `scripts/chatgpt_handoff_mcp/broker/config.py` | v3 配置、allowed roots、资源 URL |
| `scripts/chatgpt_handoff_mcp/broker/models.py` | 状态与数据类型 |
| `scripts/chatgpt_handoff_mcp/broker/policy.py` | 内容与字节限制 |
| `scripts/chatgpt_handoff_mcp/broker/store.py` | 状态、槽、收据与恢复 |
| `scripts/chatgpt_handoff_mcp/broker/service.py` | 与传输无关的 fetch/submit |
| `scripts/chatgpt_handoff_mcp/broker/auth.py` | issuer/audience/resource/scope/ACL |
| `scripts/chatgpt_handoff_mcp/server.py` | 两工具 MCP 适配 |
| `scripts/chatgpt_handoff_mcp/tests/` | 配置、策略、状态、并发、鉴权测试 |
| `scripts/chatgpt_handoff_mcp/smoke.py` | 独立 Git 项目的真实 stdio 往返 |

---

### 任务 1：冻结模型、配置和 SDK 证据

**文件：**

- 新建：`scripts/chatgpt_handoff_mcp/broker/__init__.py`
- 新建：`scripts/chatgpt_handoff_mcp/broker/models.py`
- 新建：`scripts/chatgpt_handoff_mcp/broker/config.py`
- 新建：`scripts/chatgpt_handoff_mcp/tests/test_config.py`
- 修改：`scripts/chatgpt_handoff_mcp/pyproject.toml`、`scripts/chatgpt_handoff_mcp/uv.lock`

**接口：** `HandoffState`、`Outcome`、`HandoffRecord`、`FetchEnvelope`、`ArtifactReceipt`；`load_project_config(Path) -> ProjectConfig`；`load_broker_config(Path) -> BrokerConfig`；`register_workspace(BrokerConfig, Path) -> WorkspaceRecord`。

- [ ] **步骤 1：核验版本与签名**

```sh
rg '^name = "mcp"|^version = ' scripts/chatgpt_handoff_mcp/uv.lock --line-number --context 1
npx ctx7@latest library mcp "Python FastMCP streamable HTTP authentication protected resource metadata OAuth"
npx ctx7@latest docs /modelcontextprotocol/python-sdk "FastMCP OAuth bearer authentication auth context RFC 9728 resource indicator audience validation"
```

记录实际版本、`TokenVerifier`、`AuthSettings`、受保护资源元数据和缺失能力。缺能力时保持远程禁用。

- [ ] **步骤 2：写失败测试**

覆盖 allowed root 为 `/`、主目录、临时目录、重叠根；项目越根；URL 非 HTTPS或含查询串；上限超过 `1048576`；TTL 超过 `604800`。

```python
def test_rejects_root_as_allowed_root(self):
    with self.assertRaisesRegex(ValueError, "allowed_roots"):
        load_broker_config(self.write_config(allowed_roots=["/"]))
```

运行：`uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_config -v`。预期因实现不存在而失败。

- [ ] **步骤 3：实现并验证**

配置使用冻结 dataclass；项目配置只含相对交接根、策略、上限和 TTL；用户配置才含真实根、状态目录和 OAuth。句柄用 `secrets.token_urlsafe(24)`，登记 root identity。

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_config -v
uv run --project scripts/chatgpt_handoff_mcp --locked python -m py_compile scripts/chatgpt_handoff_mcp/broker/config.py scripts/chatgpt_handoff_mcp/broker/models.py
git add scripts/chatgpt_handoff_mcp/broker scripts/chatgpt_handoff_mcp/tests/test_config.py scripts/chatgpt_handoff_mcp/pyproject.toml scripts/chatgpt_handoff_mcp/uv.lock
git commit -m "feat(handoff): add broker configuration model"
```

### 任务 2：统一策略并物化出站快照

**文件：** 新建 `broker/policy.py`、`tests/test_policy.py`；修改 `tools/chatgpt_handoff.py`。

**接口：** `validate_markdown(text, maximum_bytes, policy) -> ValidatedMarkdown`；`materialize_outbound(project_root, source_files, task, summary, config) -> ValidatedMarkdown`。

- [ ] **步骤 1：写失败测试**

覆盖中文 Markdown、UTF-8 字节边界、NUL、控制字符、原始 HTML、Base64/data URL、绝对路径、原始数据、数据集、权重、检查点、日志、凭据、服务器连接和目标期；证明删除源文件后冻结包仍可读。

```python
def test_rejects_target_period_before_writing(self):
    with self.assertRaisesRegex(PolicyViolation, "目标期信息"):
        validate_markdown("请分析目标期标签", 262144, POLICY)
```

运行：`uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_policy -v`。

- [ ] **步骤 2：实现并验证**

迁移现有敏感模式供 CLI 与 broker 共用。创建时读取明确列出的 Markdown；内部 manifest 保存相对路径，公开包只显示 `source-001`。对最终字节扫描一次并计算 SHA-256，读取时只复核哈希。

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_policy tests.test_config -v
uv run --project scripts/chatgpt_handoff_mcp --locked python tools/chatgpt_handoff.py --help
git add tools/chatgpt_handoff.py scripts/chatgpt_handoff_mcp/broker/policy.py scripts/chatgpt_handoff_mcp/tests
git commit -m "feat(handoff): materialize sanitized outbound bundles"
```

### 任务 3：实现状态、槽与收据

**文件：** 新建 `broker/store.py`、`tests/test_store.py`。

**接口：** `BrokerStore.create_handoff(...) -> HandoffRecord`；`transition(...) -> AuditReceipt`；`publish_result(...) -> ArtifactReceipt`；`retry(...) -> HandoffRecord`；`recover() -> RecoveryReport`。

- [ ] **步骤 1：写失败测试**

固定迁移矩阵：`created -> dispatched/failed/expired`，`dispatched -> running/failed/expired`，`running -> completed/failed/expired`，终态无后继。验证同哈希重放返回同一收据，异内容返回 `already_finalized`；两个线程只有一个结果；符号链接槽、root identity 漂移、过期、已有文件均在写前拒绝；收据链断裂被报告。

- [ ] **步骤 2：实现事务与恢复**

SQLite 启用外键、WAL 和立即事务。结果先写同槽临时文件，`flush`/`fsync` 后独占发布；发布前后验证真实父目录。恢复只完成可证明一致的事务，否则转 `failed` 并留收据，绝不覆盖终态。

- [ ] **步骤 3：验证并提交**

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_store -v
uv run --project scripts/chatgpt_handoff_mcp --locked python -m py_compile scripts/chatgpt_handoff_mcp/broker/store.py
git add scripts/chatgpt_handoff_mcp/broker/store.py scripts/chatgpt_handoff_mcp/tests/test_store.py
git commit -m "feat(handoff): add transactional handoff store"
```

### 任务 4：实现本地生命周期和人工降级

**文件：** 修改 `tools/chatgpt_handoff.py`；新建 `tests/test_cli.py`。

**接口：** `register --project-root`、`create --workspace-id`、`dispatch --handoff-id --subject`、`status --handoff-id --json`、`receive --handoff-id --from-file --sha256 --outcome`、`retry --handoff-id`、`collect --handoff-id`。

- [ ] **步骤 1：写失败测试**

测试不使用浏览器或网络的完整往返；命令输出无绝对路径；v2 只显式迁移；`receive` 不接受 stdin。

- [ ] **步骤 2：实现并验证**

`--from-file` 是本地管理面唯一可接收路径的位置，且不进入 MCP 或收据。`retry` 复制冻结任务生成新版本，不复制旧结果。

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_cli -v
uv run --project scripts/chatgpt_handoff_mcp --locked python tools/chatgpt_handoff.py --help
git add tools/chatgpt_handoff.py scripts/chatgpt_handoff_mcp/tests/test_cli.py
git commit -m "feat(handoff): add local broker lifecycle commands"
```

### 任务 5：实现两工具 MCP

**文件：** 新建 `broker/service.py`、`tests/test_service.py`；修改 `server.py`、`smoke.py`。

**接口：** `BrokerService.fetch(handoff_id: str, auth: AuthContext) -> FetchEnvelope`；`BrokerService.submit(handoff_id: str, markdown: str, content_sha256: str, outcome: Outcome, auth: AuthContext) -> ArtifactReceipt`。

- [ ] **步骤 1：写失败测试**

真实 `list_tools` 必须精确返回两个名称。递归检查输入模式不得出现 `path/root/url/command/attachment/file/workspace`。未知与未授权 ID 返回相同错误，响应无绝对路径。

- [ ] **步骤 2：实现并验证**

`fetch` 校验 ACL、过期和出站哈希后原子迁移 `running`。`submit` 校验身份、状态、哈希、字节和策略后调用 store。删除远程 list、manifest、profile 和 search 工具。冒烟覆盖 create/dispatch/fetch/submit/重放/collect 及穿越式 ID、错误哈希、超限和目标期负例。

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_service -v
uv run --project scripts/chatgpt_handoff_mcp --locked python scripts/chatgpt_handoff_mcp/smoke.py
git add scripts/chatgpt_handoff_mcp/broker/service.py scripts/chatgpt_handoff_mcp/server.py scripts/chatgpt_handoff_mcp/tests/test_service.py scripts/chatgpt_handoff_mcp/smoke.py
git commit -m "feat(handoff): expose two-tool handoff broker"
```

### 任务 6：实现认证和默认关闭的 HTTP 门

**文件：** 新建 `broker/auth.py`、`tests/test_auth.py`；修改 `server.py`、`pyproject.toml`、`uv.lock`。

**接口：** `AuthContext(subject, client_id, issuer, audience, scopes)`；`authorize(context, handoff, action, config) -> None`。

- [ ] **步骤 1：写失败测试**

覆盖无 bearer、过期 token、错误签名、issuer、audience、resource、subject、client、scope、ACL、query/body token、通配 host 和伪造 Forwarded 头。未授权 HTTP 必须返回 `401` 与资源元数据位置。

- [ ] **步骤 2：按已核签名实现**

实现 RFC 9728 元数据、RFC 8707 resource 和精确 audience；token 只从 Authorization header 接收且不转发。能力缺失时 `streamable-http` 启动失败并列缺失项，本地 stdio 可用。

- [ ] **步骤 3：验证并提交**

```sh
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest tests.test_auth tests.test_service -v
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest discover -s scripts/chatgpt_handoff_mcp/tests -v
git add scripts/chatgpt_handoff_mcp/broker/auth.py scripts/chatgpt_handoff_mcp/server.py scripts/chatgpt_handoff_mcp/tests/test_auth.py scripts/chatgpt_handoff_mcp/pyproject.toml scripts/chatgpt_handoff_mcp/uv.lock
git commit -m "feat(handoff): enforce broker OAuth resource boundary"
```

### 任务 7：更新安装、迁移与工作流

**文件：** 修改 `install_global.sh`、`mcp-config.example.json`、`README.md`、`.codex/skills/chatgpt-handoff/SKILL.md`、`.Codex/docs/ChatGPT交接工作流.md`。

- [ ] **步骤 1：更新内容**

分别写清 MCP 读写、只读套餐下本地 `receive`、完全无 MCP 时人工复制。隧道/HTTPS 只作为可选边界。安装器复制完整 `broker/`，不创建令牌或真实配置。

- [ ] **步骤 2：验证并提交**

```sh
CODEX_HOME=/private/tmp/chatgpt-handoff-install-smoke bash scripts/chatgpt_handoff_mcp/install_global.sh
fd . /private/tmp/chatgpt-handoff-install-smoke/tools/chatgpt-handoff --type f
rg 'list_handoffs|search_handoff_context|exec_command|write_stdin|download_artifact' scripts/chatgpt_handoff_mcp/README.md .codex/skills/chatgpt-handoff/SKILL.md .Codex/docs/ChatGPT交接工作流.md --line-number
git add scripts/chatgpt_handoff_mcp/install_global.sh scripts/chatgpt_handoff_mcp/mcp-config.example.json scripts/chatgpt_handoff_mcp/README.md .codex/skills/chatgpt-handoff/SKILL.md .Codex/docs/ChatGPT交接工作流.md
git commit -m "docs(handoff): document broker and manual fallback"
```

预期：安装文件齐全；旧能力只在禁止或迁移说明中命中。

### 任务 8：安全负例、恢复和交付门禁

**文件：** 修改 `smoke.py`、`tests/test_store.py`、`tests/test_auth.py`；新建 `.Codex/docs/2026-09-08-ChatGPT交接Broker实施报告.md`。

- [ ] **步骤 1：运行完整验证**

```sh
rg 'subprocess|os\.system|create_subprocess|exec_command|write_stdin|apply_patch|download_artifact' scripts/chatgpt_handoff_mcp/broker scripts/chatgpt_handoff_mcp/server.py --line-number
uv run --project scripts/chatgpt_handoff_mcp --locked python -m unittest discover -s scripts/chatgpt_handoff_mcp/tests -v
uv run --project scripts/chatgpt_handoff_mcp --locked python scripts/chatgpt_handoff_mcp/smoke.py
uv run --project scripts/chatgpt_handoff_mcp --locked python -m py_compile tools/chatgpt_handoff.py scripts/chatgpt_handoff_mcp/server.py scripts/chatgpt_handoff_mcp/broker/*.py
git diff --check
git status --short
```

预期：能力面检查零命中；状态、幂等、并发、过期、敏感内容、路径替换、错误受众、错误资源和 MCP 往返通过；无临时数据库、令牌或结果正文。

- [ ] **步骤 2：写报告并提交**

报告分别标记“本地实现通过”“远程认证静态通过”“真实 ChatGPT 端到端未验证”。未执行隧道、公开 HTTPS、真实 OAuth 或渗透测试时，不得写“已部署”或“安全”。

```sh
git add .Codex/docs/2026-09-08-ChatGPT交接Broker实施报告.md scripts/chatgpt_handoff_mcp/smoke.py scripts/chatgpt_handoff_mcp/tests/test_store.py scripts/chatgpt_handoff_mcp/tests/test_auth.py
git commit -m "test(handoff): verify broker security boundaries"
```

## 顺序与停止条件

1. 任务 1 至 5 先形成本地 stdio 与人工流程可运行的最小系统。
2. 任务 6 是远程硬门。OAuth、资源 URL 或套餐任一未核验时保持远程禁用。
3. 发现可选路径、覆盖、额外工具、shell/exec、敏感正文入收据或 ID 存在性泄漏时，立即停止远程发布。
4. 计划完成不等于获准部署；Secure MCP Tunnel 或 HTTPS 须另行明确批准。

## 自审结果

- 覆盖：allowed roots、两级句柄、六态、哈希、字节上限、一次提交、新版本、跨项目配置、收据、OAuth/资源 URL、远程边界和人工降级均有任务。
- 占位：命令、接口和报告路径均已具体化。
- 类型：`HandoffState`、`Outcome`、`AuthContext`、`HandoffRecord`、`FetchEnvelope`、`ArtifactReceipt` 前置定义并一致复用。
- 范围：不安装 DevSpace、不改研究代码、不运行实验、不部署公网服务。

## 执行交接

主代理与用户批准后，推荐用 `superpowers:subagent-driven-development` 按任务 1 至 8 执行并逐项复核；当前会话批量执行则用 `superpowers:executing-plans`，仍不得跳过任务 6。
