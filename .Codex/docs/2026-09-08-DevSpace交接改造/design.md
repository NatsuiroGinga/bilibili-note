# 普通 ChatGPT 与 Codex 通用交接 Broker 设计

日期：2026-09-08
状态：设计可行，尚未实现、未部署、未完成对抗性验证
分类：`architectural`

## 1. 结论

推荐在现有 `chatgpt-handoff-readonly` 代码基础上演进出一个**单服务、双动作、句柄驱动的 `chatgpt-handoff-broker`**，而不是同时公开只读服务和写入服务。公网 MCP 只注册两个工具：

1. `fetch_handoff(handoff_id)`：按高熵句柄返回已经物化、脱敏、冻结且未过期的单个出站包。
2. `submit_handoff_result(handoff_id, markdown, content_sha256, outcome)`：向创建出站包时预留的 inbox 槽提交一次受限 Markdown；`outcome` 只允许 `completed` 或 `failed`。

`list_handoffs`、`search_handoff_context`、任意路径读取、附件上传、shell、命令执行、补丁、Git、进程会话和目录遍历均不得进入远程工具面。现有只读原型可以保留为本地 `stdio` 兼容入口，但不得与远程 broker 共用公开地址或 OAuth 客户端配置。

该方案只借鉴 DevSpace 的 `allowedRoots`、工作区句柄、长任务状态、制品收据和 OAuth 资源 URL 校验思路，不复制其文件编辑、命令执行、进程会话、附件下载或公共开发机入口。本文不声称 DevSpace 或本方案已经安全。

## 2. 目标与非目标

### 2.1 目标

- 浏览器自动控制、桌面自动化或 GitHub 应用不可用时，普通 ChatGPT 与 Codex 仍可凭 `handoff_id` 交换一个冻结任务和一个结果。
- 支持任意已注册 Git 项目，不把项目绝对路径写入客户端配置、提示词、令牌或收据。
- 长任务具有明确、幂等且可审计的 `created`、`dispatched`、`running`、`completed`、`failed`、`expired` 状态。
- 出站与入站内容均有 SHA-256、字节数、策略版本、时间和状态迁移收据。
- 写入只能落到服务端预创建的单个 inbox 槽，既不能选路径，也不能覆盖既有结果。

### 2.2 非目标

- 不提供远程开发环境、代码执行器、文件浏览器、通用上传器或多代理运行平台。
- 不允许 ChatGPT 核验原始日志、权重、检查点、数据集、目标期信息、服务器状态或权威哈希。
- 不自动采纳外部结果，不改代码、Git、实验、恢复卡、论文结论或冻结合同。
- 本任务不安装 DevSpace、不修改生产代码、不部署公网服务、不验证 ChatGPT 端到端连接。

## 3. 不可让渡的安全边界

### 3.1 远程能力白名单

远程 MCP 的工具清单必须精确等于：

```text
fetch_handoff
submit_handoff_result
```

服务端进程不得导入或调用 `subprocess`、shell、Git、终端、工作树创建、任意 URL 下载或文件上传逻辑。客户端参数不得出现 `path`、`root`、`workspace_path`、`output_path`、glob 或目录名。

### 3.2 内容边界

- 出站只包含创建时物化为单个 UTF-8 Markdown 的脱敏快照。远程请求期间不再读取源文件。
- 入站只接受 UTF-8 Markdown 文本，不接受附件、二进制、Base64 数据块、数据 URL、MIME 多段内容或外部资源抓取指令。
- 出站和入站各自最大 `262144` 字节。该值是初始工程安全上限，不是科研参数；实施阶段须用真实请求峰值和隧道限制核验，任何调整不得超过全局硬上限 `1048576` 字节。
- 继续拒绝原始数据、数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、未授权目标期信息和疑似秘密。
- Markdown 按纯文本保存和展示，不在 broker 内执行代码块、不解析本地链接、不启用原始 HTML。

### 3.3 路径与写入边界

- `allowed_roots` 仅由本机管理员配置，远程客户端不可读取或修改。
- 项目注册时把真实根路径映射为随机 `workspace_id`；出站创建时再生成随机 `handoff_id`。两者均使用不少于 128 位熵的 Base64URL 值，不由文件名、路径或仓库名推导。
- 每个交接在服务端创建一个专属槽目录，包含不可变 `slot.json`；最终结果只允许以独占创建方式生成一次 `result.md`。
- 写入前重新验证槽目录真实路径仍位于已登记交接根、不是符号链接，目标文件不存在，状态允许迁移，内容哈希与请求一致。
- 远程客户端从不提交路径。`handoff_id` 只用于数据库查表，且句柄本身不构成授权。

### 3.4 外部候选边界

所有回收结果自动带入不可删除的服务端元数据：`外部候选，待本地全文和实验复核`。该标记写入收据与本地状态，不依赖 ChatGPT 自觉输出。后续是否引用仍由 Codex 按项目规则独立复核。

## 4. 方案比较

### 4.1 方案 A：演进为单一窄写 broker，推荐

复用现有 Python MCP 项目、脱敏策略和项目初始化入口，但更换公开工具面和存储模型。远程只保留取包与单次提交；状态、路径、收据和版本由同一事务边界管理。

优点：

- 只有一个 OAuth 资源 URL、一个受众、一个状态存储和一个审计序列。
- 读取与写入可在同一事务中验证同一个 `handoff_id`、过期时间、策略版本和终态。
- 可复用当前 CLI、敏感模式、`127.0.0.1` 默认绑定和 uv 项目，迁移成本最低。

代价：

- 服务名称和现有只读兼容预期会变化。
- 必须删除远程 `list_handoffs` 与跨文件搜索，不能只是给当前服务追加写工具。
- 写入端缺陷会影响同一进程内的读取，因此必须加强事务、独占写与权限测试。

### 4.2 方案 B：拆成只读服务和写入服务，不推荐

保留当前只读 MCP，再新增独立写入 MCP，由两个服务共享或同步交接状态。优点是部署者可物理关闭写服务，读写代码也可独立发布。代价是需要两套资源 URL、OAuth 客户端或受众、隧道、健康检查和版本兼容；共享数据库会扩大耦合，分离数据库又会引入状态竞争、过期不同步和重复提交判定歧义。当前只有一个读动作和一个写动作，收益不足以抵消这些风险。

### 4.3 方案 C：维持纯人工或 GitHub 复制，不作为目标架构

该方案攻击面最小，且应继续作为最终降级路径，但不能提供可靠的长任务状态、幂等提交与机器可核验收据。它适合作为远程 MCP 不可用时的保底，不替代 broker。

## 5. 总体架构

```text
本地 Codex/CLI
  | register/create/dispatch/status/retry/receive
  v
本地管理面 -------------------------------+
  |                                      |
  | 冻结出站包、预创建 inbox 槽            | 状态与审计收据
  v                                      v
项目内 handoff 根                    用户级状态目录
  | outbox/<id>/request.md               | workspace 映射
  | inbox/<id>/slot.json                 | 状态数据库
  | inbox/<id>/result.md                 | 追加式收据
  +------------------+-------------------+
                     | 仅服务端映射
                     v
127.0.0.1 上的 MCP broker
  | fetch_handoff / submit_handoff_result
  v
可选 Secure MCP Tunnel 或固定 HTTPS 反向代理
  | OAuth 2.1、资源 URL、受众与交接 ACL
  v
普通 ChatGPT 自定义 MCP 应用
```

本地管理面与远程数据面必须分开。`register`、`create`、`dispatch`、`retry`、`expire` 和人工 `receive` 只通过本机 CLI 提供，不注册为 MCP 工具。

## 6. 数据模型与可移植配置

### 6.1 项目配置

项目内 `.chatgpt-handoff.json` 升级为 `chatgpt-handoff-v3`，只保存可移植、非敏感、相对项目根的字段：

```json
{
  "schema_version": "chatgpt-handoff-v3",
  "handoff_root": ".Codex/docs/chatgpt-handoffs",
  "policy_profile": "research-sanitized-v1",
  "max_outbound_bytes": 262144,
  "max_result_bytes": 262144,
  "default_ttl_seconds": 86400,
  "max_ttl_seconds": 604800
}
```

用户级配置保存 `allowed_roots`、固定 `public_mcp_url`、OAuth issuer、允许客户端、状态目录和代理信任边界。它不进入 Git。不同机器只需重新注册项目并生成新的 `workspace_id`，项目配置无需改绝对路径。

### 6.2 服务端工作区登记

```text
workspace_id
project_root_realpath
handoff_root_relative
root_identity
enabled
created_at
```

`root_identity` 在支持的平台记录设备与 inode 或等价文件标识，用于发现根目录被替换。`allowed_roots` 拒绝 `/`、用户主目录本身、临时目录、凭据目录和彼此含混的重叠根。

### 6.3 交接记录

```text
handoff_id
workspace_id
version
predecessor_handoff_id
state
outbound_sha256
outbound_bytes
result_sha256
result_bytes
policy_version
created_at
dispatched_at
running_at
finished_at
expires_at
authorized_subject
```

出站包的相对源路径只保存在服务端 manifest。默认向 ChatGPT 展示 `source-001` 这类逻辑标签；确需展示仓库相对路径时，必须在本地创建阶段明确选择且通过脱敏策略。

## 7. 状态机与幂等语义

```text
created -> dispatched -> running -> completed
    |           |           |------> failed
    |           |------------------> expired
    |------------------------------> expired
```

- `created`：本地 CLI 已写出冻结出站包、manifest 和预创建槽。
- `dispatched`：本地所有者显式执行 `dispatch`，此后授权主体可读取。
- `running`：第一次成功 `fetch_handoff` 后由服务端原子迁移；重复读取不再改变状态。
- `completed`：提交 `outcome=completed` 的单个 Markdown 成功。
- `failed`：提交 `outcome=failed` 的单个 Markdown，或本地所有者显式终止。
- `expired`：服务端在每次访问前比较 `expires_at`，或本地清理器标记过期。

`completed`、`failed`、`expired` 为终态。相同 `handoff_id`、相同 `content_sha256`、相同 `outcome` 的重复提交返回原收据，不二次写文件；不同内容或不同结果状态返回 `already_finalized`。需要修改结果时，本地所有者执行 `retry`，创建 `version+1` 的新 `handoff_id`、新槽与 `predecessor_handoff_id`，旧结果永不覆盖。

状态更新与 `result.md` 发布采用单事务意图：先校验并写同目录临时文件，刷新文件，独占发布，再提交数据库终态和收据。启动恢复程序只允许完成可证明的一致事务或将其标为 `failed`，不得覆盖终态文件。

## 8. MCP 接口

### 8.1 `fetch_handoff`

输入：

```json
{"handoff_id": "高熵不透明句柄"}
```

输出只含 `handoff_id`、`state`、`version`、`expires_at`、`outbound_sha256`、`outbound_bytes`、`policy_version` 和 `markdown`。不存在、未授权、已过期的句柄统一返回不泄露存在性的错误。工具不得返回本机路径、仓库根、allowed root 或 inbox 位置。

### 8.2 `submit_handoff_result`

输入：

```json
{
  "handoff_id": "高熵不透明句柄",
  "markdown": "受限 Markdown",
  "content_sha256": "64 位小写十六进制",
  "outcome": "completed"
}
```

输出只含 `receipt_id`、`handoff_id`、`version`、`state`、`content_sha256`、`content_bytes`、`submitted_at` 和 `idempotent_replay`。服务端重新计算 SHA-256；不一致、超限、策略拒绝、状态非法或未授权均不写槽。

### 8.3 刻意不提供的接口

不提供 list、search、read path、write path、upload、download、patch、exec、stdin、Git、workspace open、worktree、heartbeat 或取消工具。长任务状态通过首次读取进入 `running`、终态提交和过期机制表达，不允许客户端用任意进度文本反复写本机。

## 9. OAuth、资源 URL 与远程部署边界

默认运行方式仍是本地 `stdio` 或仅监听 `127.0.0.1`。ChatGPT 不能直接连接本机 MCP；需要远程端点。OpenAI 当前文档说明，私网或开发机可通过 Secure MCP Tunnel 接入支持的产品，写入能力的套餐和界面可用性仍可能变化，因此部署前必须重新核验。[OpenAI 开发者模式与 MCP 应用说明](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt)

远程启用必须同时满足：

- `public_mcp_url` 是配置中冻结的精确 HTTPS 规范 URL，例如 `https://broker.example/mcp`，禁止通配主机、查询串、片段和运行时 Host 推导。
- 实现 RFC 9728 受保护资源元数据；未授权请求在 HTTP 边界返回带 `resource_metadata` 的 `401`。
- 授权请求和令牌请求携带 RFC 8707 `resource`；资源服务器验证令牌 issuer、签名、过期时间、受众精确等于规范 MCP URL，以及读写 scope 和 `handoff_id` ACL。MCP 规范明确要求资源指示与受众校验。[MCP 授权规范](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- 不转发客户端 bearer token，不接受 query/body token，不把 token、授权码、Cookie 或完整请求体写入日志。
- 反向代理头只在请求来自固定可信代理地址时接受；否则忽略 `Forwarded` 与 `X-Forwarded-*`。
- 每次发布应用后核对 ChatGPT 冻结的工具快照精确等于两个工具；工具模式变更必须重新审核。
- Secure MCP Tunnel 是优先选项；自建 HTTPS 仅适用于能管理证书、固定域名、访问控制、速率限制和补丁周期的环境。

若当前套餐或模式只支持读取，继续使用 `fetch_handoff`，结果通过本地 `receive --handoff-id --from-file` 进入同一个验证器和预创建槽。深度研究当前只使用自定义应用的读动作，因此不可依赖它直接提交结果；此事实部署前须重新核验。

## 10. 威胁模型

| 威胁 | 主要后果 | 强制缓解 | 剩余风险 |
| --- | --- | --- | --- |
| ChatGPT、网页或来源文档中的提示注入 | 诱导越权读取、提交秘密或执行动作 | 工具面只有按 ID 取包和单次文本提交；无路径、shell、上传和 URL 抓取 | 模型仍可能在 Markdown 中生成不当内容，需入站策略与后续人工复核 |
| `handoff_id` 泄漏或猜测 | 未授权读取或提交 | 128 位以上随机句柄、OAuth 身份、每交接 ACL、短期过期；句柄不当凭据 | 已授权主体账户或 bearer 被盗仍可调用 |
| bearer 重放或资源混淆 | 跨服务使用令牌 | HTTPS、精确 issuer/audience/resource 校验、短期令牌、禁止 token passthrough | Bearer 在有效期内被盗仍可重放，需身份提供方告警与撤销 |
| 路径穿越、符号链接替换、根目录漂移 | 读写项目外文件 | 客户端无路径；真实路径、root identity、槽父目录和非符号链接复核；独占创建 | 本机同账户恶意进程仍可能竞争，建议单用途账户 |
| 重复或并发提交 | 覆盖结果、状态分叉 | 内容哈希幂等、数据库事务、文件独占创建、终态不可逆 | 文件系统或数据库故障需恢复扫描 |
| 超大 Markdown 或二进制伪装 | 内存、磁盘和隧道耗尽 | HTTP body 限制、UTF-8 与控制字符检查、262144 字节限制、速率限制 | 大量不同有效句柄仍需全局配额 |
| 敏感信息进入出站或结果 | 数据泄漏或不当持久化 | 创建时单次机械预检、不可变快照、服务时复核哈希；入站单次策略扫描；不支持附件 | 正则不能证明无秘密，发起方仍须只选脱敏来源 |
| 目标期信息被交接 | 研究泄漏 | 任务类型策略、目标期词与字段拒绝、源期摘要专用合同 | 隐晦表达可能绕过机械规则，最终责任留在本地发起方 |
| 审计日志自身泄密 | 暴露内容、路径或身份 | 收据只存哈希、字节数、事件、主体哈希和时间，不存正文、令牌、绝对路径或原始请求 | 时间和大小仍是元数据，应限制本机访问 |
| 远程服务配置错误 | 暴露额外工具或错误主机 | 启动时验证固定 URL、非通配 host、精确工具清单和 OAuth 元数据；失败即不监听 | 隧道和身份提供方仍属外部信任边界 |

## 11. 制品与审计收据

每个状态迁移生成 append-only JSON 收据，最少字段为：

```text
receipt_id, previous_receipt_sha256, event, workspace_id, handoff_id, version,
old_state, new_state, outbound_sha256, result_sha256, content_bytes,
policy_version, actor_subject_sha256, oauth_client_id_sha256, occurred_at
```

收据不保存正文、令牌、个人绝对路径、IP、完整 User-Agent、仓库远端或客户端自由文本。收据先写用户级状态目录，再可由本地 CLI 导出一个脱敏 sidecar 到交接目录。任何导出都由本地所有者执行，远程客户端不能选导出位置。

## 12. 无浏览器控制时的交换流程

1. Codex 本地运行 `create`，物化脱敏出站包并预创建 inbox 槽，得到 `handoff_id`。
2. Codex 本地运行 `dispatch`，把状态从 `created` 改为 `dispatched`，并只向用户显示句柄和到期时间。
3. 用户在普通 ChatGPT 对话中手动给出句柄；ChatGPT 经已审核 MCP 调用 `fetch_handoff`，不需要 Codex 控制浏览器。
4. 支持写入时，ChatGPT 调用 `submit_handoff_result`；不支持写入时，用户保存 Markdown，本地执行 `receive --handoff-id --from-file`，走同一策略、哈希、槽位和收据逻辑。
5. Codex 运行 `status` 或 `collect`，只按句柄回收结果并进行本地复核。

该流程保留人工复制作为最终降级，不因 MCP、隧道、套餐或浏览器功能失效而改用 Work/Codex 冒充普通 ChatGPT。

## 13. 验收条件

### 13.1 功能

- 任意已注册 Git 项目均能创建、派发、读取、提交、回收和显式创建新版本。
- 浏览器自动化关闭时，凭句柄和手工操作仍能完成往返。
- 六种状态及全部允许和拒绝迁移有确定性测试。
- 相同提交重放返回同一收据；不同提交不能覆盖。

### 13.2 安全

- 远程工具名集合精确等于两个允许工具。
- 请求模式不包含路径、命令、URL、附件或工作区打开参数。
- 路径穿越、符号链接、过期、越权、错误受众、错误资源 URL、超限、二进制、目标期和敏感文本均在写文件前拒绝。
- 服务端代码无 shell/exec/subprocess 调用，默认只绑定 `127.0.0.1`。

### 13.3 审计与恢复

- 每次状态迁移都生成可验证哈希链收据。
- 模拟进程在临时文件发布、独占创建和数据库提交之间退出后，恢复结果不覆盖终态、不产生两个不同结果。
- 收据和 MCP 响应均不泄露绝对路径或正文。

## 14. 尚未证明的事项

- 未验证当前 Python MCP SDK 版本对完整 OAuth 2.1、RFC 9728、RFC 8707 与 Secure MCP Tunnel 的具体适配接口；实现前必须按目标安装版本查官方文档。
- 未验证 ChatGPT 当前账户、模式和管理员策略是否允许写入 MCP；部署前以界面和官方文档为准。
- 未进行渗透测试、依赖漏洞审计、隧道故障演练、跨平台文件系统竞争测试或真实负载测量。
- 机械脱敏只能拒绝已知模式，不能证明任意自然语言都不含秘密。因此源材料选择和回收复核仍留在 Codex 本地。

## 15. 本次不变范围

本设计不修改 `tools/chatgpt_handoff.py`、`scripts/chatgpt_handoff_mcp/`、现有 Skill、既有交接包、Git 状态或任何远程服务。后续实现必须先获得用户批准，并按 [实施计划](implementation-plan.md) 分阶段完成。
