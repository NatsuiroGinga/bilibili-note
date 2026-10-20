---
name: invoke-skills-not-guess-from-names
description: 用 Skill 工具真正加载技能，不要凭技能名猜内容就动手；派子代理时把链路写进简报并要求它显式调用
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a6b7721f-65a8-411a-9630-071c1601ca01
  modified: 2026-08-19T03:43:49.323Z
---

**要用技能就用 `Skill` 工具真正加载它，不要把技能名当成它内容的摘要然后照摘要自己做。** 派子代理时同样：把技能链路写进简报还不够，必须明确要求它用 `Skill` 工具显式调用。

**Why:** 2026-08-18 至 08-19 的第三章定稿会话，全程 `Skill` 调用次数为**零**，而每一轮 hook 都在提醒技能编排。表现出三种形态。

其一，**主代理凭名字行事**。看到 `citation-verification` 就理解成「仔细核验引注」然后去仔细核验，从没打开看过它写了什么。整晚向用户复述 `paper-self-review` 的「六项裁定」，那是从仓库 `AGENTS.md` 的转述读来的。真正加载后发现：六项的名字对，但**漏了技能规定的 `Claim Audit` 输出结构**（`Claim` / `Verdict: keep|weaken|revise|remove` / `Evidence used` / `Missing evidence` / `Overclaim risk` / `Suggested wording`），而仓库 `AGENTS.md` 明写「输出用技能规定的 `Claim Audit` 结构」——**它把格式委托给技能，我从没去取**。另有三份引用文件（`SECTION-CHECKLIST.md`、`FINAL-VERDICT.md`、`example-self-review.md`）始终未加载。后果是本会话处置过的全部论断（撤超可加、改收敛措辞、删随机森林半句）**都没有按统一结构记录**，散在对话与各份报告里。

其二，**派子代理时整条链路漏掉**。派 Fable 做第四章候选分析时，任务同时命中「机制构思」与「文献」两个阶段，两条链路一条都没写进简报。特别不该漏的是 `brainstorming` 属仓库限制使用的技能，第四章候选正是它唯一合法场景。

其三，**写了名字但没要求调用**。派第一二章文献工作流时把 `planning-with-files → literature-reviewer → citation-verification` 写进了简报，但没说「用 `Skill` 工具调用」。实测结果：代理已启动而任务目录 `task_plan.md` 与 `notes.md` **始终未建立**，即该技能根本没生效。

**根因与已记在案的另一条同型**：这与同一会话写进故障预防手册的「用先验概率替代可执行的核验」是同一个 bug——那次是用「先验上不太可能出错」替代核验，实际二十个差值里三个是错的且全落在未核验批次；这次是用对技能名的猜测替代技能的实际约束。**替代的对象不同，机制相同：拿手边的近似当成了本体。**

**How to apply:** 触发条件是 hook 给出了阶段与应调技能、或任务落在 `AGENTS.md` 技能编排表的任一阶段。此时先用 `Skill` 工具加载，再动手；技能有引用文件的，按需加载后再执行，不要凭主文档猜引用文件的内容。派子代理时把「用 `Skill` 工具显式调用，跳过链路属违规，与仓库规则冲突须显式说明冲突点与采纳理由」写进简报，并在其返回中要求说明各技能的实际调用情况与产出落点。已发生的三次都是用户提醒后才补，成本转嫁给了用户。相关：[[consult-sources-before-asserting]]、[[check-gates-and-contracts-before-scoping]]、[[record-fixed-bugs-into-rules]]。
