---
name: fuse-safeguards-into-the-action
description: "保全措施要焊进动作本身，独立的\"记得启动\"工具必然会被忘掉"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bf71861-639f-455d-b431-5dbc10e3331a
  modified: 2026-09-01T06:25:19.429Z
---

存在一个需要「记得单独启动」的保全工具，等于没有保全。**把它焊进它所保护的那个动作**：
起训练的命令必须同时起回传，做不到分离才算修好。

**Why**：2026-09-01 水库筛选臂在服务器整轮跑完，随后服务器关机，本机 `0` 个制品。
而 `watch_and_pull_ch3_ft.sh`（每 5 分钟拉制品）**早就存在**，恢复卡第 88 行白纸黑字写着，
它正是为「服务器保存唯一副本」这个已发生过一次的事故建的。我从头到尾没起它。
用户的反应是「我真的无语了」。这是同类事故第二次。

修法是新增 `scripts/remote_launchers/launch_run_with_pull.sh` 作为**唯一训练入口**，
启动训练的同时起回传守护，并在 `scripts/AGENTS.md` 写死「禁止直接 nohup uv run --run」。

**How to apply**：看到「工具已存在，只要记得用」这种情况，就是危险信号——
问「能不能让它不用记也会发生」。能焊进去就焊，焊不进去就加机械断言，
最差也要写进最近层的 AGENTS.md 而不是只写进文档。
相关：[[make-it-mechanical-not-remembered]]、[[commit-before-editing-any-document]]。
