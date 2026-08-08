# rust-skills 安装验收报告

## 结论

- **状态：安装完成，确定性发现检查通过。**
- 安装路径：`/Users/bilibili/.codex/skills/rust-skills`
- 技能名称：`rust-skills`
- 技能版本：`1.5.1`
- 来源仓库：`leonardomso/rust-skills`
- 来源分支：`master`
- 验收时远端提交：`fd2a861ab0406a4ac536a55274d14ea6fd1ca9c9`
- 安装方式：仅使用 Codex 官方 `skill-installer` 脚本，没有手工复制文件，也没有覆盖既有目录。

## 任务边界

- 新增用户级技能目录：`/Users/bilibili/.codex/skills/rust-skills`
- 新增本报告：`.Codex/docs/2026-07-31-rust-skills安装验收.md`
- 未修改论文正文、实验代码、实验配置、运行制品和恢复文档。
- 未访问或修改服务器实验状态，因此没有阻塞主实验。
- 报告及命令记录不含密码、令牌或其他凭据。

## 安装过程

### 既有目录检查

安装前执行：

```bash
test -e /Users/bilibili/.codex/skills/rust-skills
```

结果：退出码 `1`，目标目录不存在，可以安全安装。

### 首次失败与根因

首次按默认参数执行官方脚本：

```bash
python3 /Users/bilibili/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo leonardomso/rust-skills \
  --path . \
  --name rust-skills
```

结果：退出码 `1`。脚本在临时目录的回退克隆阶段报告目标目录已经存在且非空。失败后再次检查目标安装路径，确认它仍不存在，没有留下半安装目录。

根因核验命令：

```bash
git ls-remote --symref https://github.com/leonardomso/rust-skills.git HEAD
```

核验结果显示仓库默认分支为 `master`，而官方安装脚本默认请求 `main`。脚本在 `main` 下载失败后进入 Git 回退路径，并复用首次失败留下的临时克隆目录，因此出现临时目录冲突。问题不在 `--path .`；仓库根目录确实包含有效的 `SKILL.md`，所以没有改用手工复制或猜测子路径。

### 成功安装

显式指定已核实的默认分支后重新执行官方脚本：

```bash
python3 /Users/bilibili/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo leonardomso/rust-skills \
  --path . \
  --name rust-skills \
  --ref master
```

结果：退出码 `0`，脚本输出：

```text
Installed rust-skills to /Users/bilibili/.codex/skills/rust-skills
```

## 入口与元数据验收

入口文件：`/Users/bilibili/.codex/skills/rust-skills/SKILL.md`

frontmatter 核对结果：

- 起始分隔符位于第 `1` 行，结束分隔符位于第 `20` 行。
- `name: rust-skills` 与目标目录名完全一致。
- `description` 非空，描述了 Rust 编写、审查与重构的触发范围。
- `license: MIT`。
- `metadata.author: leonardomso`。
- `metadata.version: "1.5.1"`。
- Codex 模型可见提示能够解析该 frontmatter，并将其注册为 `rust-skills`。

入口文件 SHA-256：

```text
5a74070e740c8aacec1264adfc537daeab14c0f629bb604943295c08fd9252e6
```

## 文件清单验收

使用 `fd` 逐项枚举安装目录，结果如下：

- 文件总数：`285`
- 规则文件：`265`
- 非规则支持文件：`20`
- 目录：`.github/`、`.github/workflows/`、`checks/`、`checks/src/`、`rules/`
- 未包含安装过程的 `.git/` 目录。

非规则支持文件完整清单：

```text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
README.md
SKILL.md
checks/.gitignore
checks/Cargo.lock
checks/Cargo.toml
checks/README.md
checks/analyze.py
checks/baseline.txt
checks/check.sh
checks/gen.py
checks/gen_index.py
checks/rust-toolchain.toml
checks/src/lib.rs
checks/validate.py
```

`rules/` 下的 `265` 个 Markdown 文件按前缀统计如下；合计与 `SKILL.md` 声明一致：

| 前缀 | 数量 | 前缀 | 数量 |
|---|---:|---|---:|
| `anti` | 15 | `api` | 17 |
| `async` | 18 | `closure` | 5 |
| `coll` | 4 | `conc` | 4 |
| `const` | 4 | `conv` | 3 |
| `doc` | 12 | `err` | 12 |
| `lint` | 13 | `macro` | 8 |
| `mem` | 17 | `name` | 16 |
| `num` | 5 | `obs` | 7 |
| `opt` | 12 | `own` | 12 |
| `pat` | 5 | `perf` | 13 |
| `proj` | 14 | `serde` | 8 |
| `test` | 15 | `trait` | 6 |
| `type` | 13 | `unsafe` | 7 |

## 结构与索引校验

执行仓库自带的只读校验：

```bash
cd /Users/bilibili/.codex/skills/rust-skills
python3 checks/validate.py
```

结果：退出码 `0`。

```text
OK: 265 rules valid; index lists all 265 of them.
```

该检查覆盖规则文件标题、摘要、必要章节、规则间链接，以及 `SKILL.md` 索引与全部规则文件的一致性。

## 新会话发现检查

本机存在 Codex 命令：`/opt/homebrew/bin/codex`，版本为 `codex-cli 0.144.5`。

先启动了一个全新、临时、只读的 Codex 会话：

```bash
codex exec \
  --ephemeral \
  --sandbox read-only \
  -C /private/tmp \
  --skip-git-repo-check \
  --color never \
  "检查当前新会话的技能列表中是否存在 rust-skills"
```

当前外层沙箱首次阻止了应用服务器初始化；升级到获准权限后，新会话成功启动。该模型的自然语言回答为 `NOT FOUND rust-skills`，但这与随后直接检查到的模型输入不一致，因此不把该自然语言判断作为验收依据。

随后使用 Codex 自带的确定性调试命令渲染新会话的模型可见提示：

```bash
cd /private/tmp
codex debug prompt-input "技能发现检查"
```

结果：退出码 `0`，模型可见的技能列表明确包含：

```text
- rust-skills: Comprehensive Rust coding guidelines ... (file: r0/rust-skills/SKILL.md)
```

这项检查直接证明新进程已经扫描用户技能根目录、成功解析 `SKILL.md`，并把技能注册到新会话可见列表。相较模型对列表的自然语言复述，`prompt-input` 是更直接且可复现的发现证据。

## 验收命令汇总

| 检查 | 结果 |
|---|---|
| 安装前目标目录不存在 | 通过，退出码 `1` 表示不存在 |
| 官方安装脚本，显式 `--ref master` | 通过，退出码 `0` |
| `SKILL.md` 存在且 frontmatter 可解析 | 通过 |
| frontmatter 名称与目录名一致 | 通过，均为 `rust-skills` |
| 全文件枚举 | 通过，共 `285` 个文件 |
| 规则文件计数 | 通过，共 `265` 个 |
| `python3 checks/validate.py` | 通过，退出码 `0` |
| 新 Codex 模型可见提示检查 | 通过，发现 `r0/rust-skills/SKILL.md` |

## 风险与局限

- 仓库使用 `master` 而非安装器默认的 `main`；未来重装或更新时仍应显式传入 `--ref master`，除非上游已更改默认分支。
- 新会话的模型曾对已注入列表给出一次假阴性自然语言判断。确定性的 `codex debug prompt-input` 已证明技能实际进入模型可见提示，但模型是否在具体 Rust 请求中正确触发仍取决于请求语义和当次技能选择。
- 本次只运行结构、链接、索引和发现检查，没有生成 `checks/examples/` 或运行完整 Rust 示例编译；这些属于上游技能内容质量检查，不是安装与发现的必要条件。

