# 本机联网通路实测（2026-10-14）

> 目的：把「哪个工具能上网、怎么写」固化成机械事实，避免把**可达误判为不可达**从而污染
> 「未发现／不存在」这类结论。

## 一、实测结果

| 目标 | 方式 | 结果 |
| --- | --- | --- |
| `https://huggingface.co/api/...` | `curl` 直连 | ❌ `curl: (35) Recv failure: Connection reset by peer` |
| `https://huggingface.co/api/...` | **`curl -x http://127.0.0.1:7890`** | ✅ **HTTP 200** |
| `https://arxiv.org/abs/...` | `curl` 直连 | ✅ HTTP 200 |
| `https://huggingface.co/...` | Claude 的 `WebFetch` 工具 | ❌ 报「Unable to verify if domain is safe to fetch」 |
| `https://huggingface.co/api/...` | Python `urllib`（无显式代理） | ✅ **HTTP 200** |

## 二、结论与用法

- **HuggingFace 及被重置的站点：走本机代理。**
  ```bash
  curl -sS --max-time 30 -x http://127.0.0.1:7890 "<URL>"
  curl -sS -o /dev/null -w '%{http_code}\n' --max-time 30 -x http://127.0.0.1:7890 "<URL>"   # 只要状态码
  ```
- **arXiv 等：可直连，不加 `-x`。**
- **`WebFetch` 对 HuggingFace 不可用**；报「domain is safe to fetch」时**不要据此判定来源不可得**，换 `curl -x` 或 Python `urllib` 重试。

## 三、两个必须记住的坑

1. **shell 里 `env | rg -i http_proxy` 是空的**——代理变量没有导出，所以 `curl` 不会自动走代理，
   **必须显式加 `-x http://127.0.0.1:7890`**。
2. **Python `urllib` 不显式设代理却能通**，与 `curl` 行为不一致。**同一 URL 换工具可能结果相反**，
   故「某工具取不到」不等于「该 URL 不可达」。**下「未发现／不存在」这类结论前，必须换第二种工具复核。**

## 四、与既有规则的关系

仓库根 `AGENTS.md` 有一节「本机代理劫持 DNS 时的绕过（2026-09-02 实测有效）」，
描述的是**另一种症状**（`dig` 返回 `198.18.0.0/15` 假地址、SSH/rsync 超时）。
本节补充的是 **HTTP 工具层的通路差异**，两者可并存。

**若用户同意，可把本节的「`curl -x http://127.0.0.1:7890` + 换工具复核」两条提升进根 `AGENTS.md`。**
本次只落盘在此，不擅自改规则文件。

## 五、边界

- 代理地址 `127.0.0.1:7890` 由 2026-09-02 事故记录中的既有配置推得并实测通过；
  **若用户更换代理软件或端口，本节须重测。**
- 单次实测，未做稳定性与限速测试。
