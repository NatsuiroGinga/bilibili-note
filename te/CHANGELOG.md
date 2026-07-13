---
title: bili-tellurium 版本历史
date: 2026-07-13
tags:
  - te
  - CHANGELOG
---

# bili-tellurium 版本历史

### v1.5.9

1. 从 et 大仓拆分成独立仓库
2. 修复漏洞 https://sec-dep-check.bilibili.co/s/epelcx
3. 修复 lint

### v1.5.8

1. 升级 beego/v2，从 v2.0.4 到 v2.2.1，修复漏洞 https://sec-src.bilibili.co/bug/detail?vul_id=31545

### v1.5.7

1. go.mod go 版本到 go1.20

### v1.5.6

1. 升级 go-common 到 v1.46.1

### v1.5.5

1. 更新 go.mod

### v1.5.4

1. invalid isp 告警仅对 Normal 状态机器生效
2. 添加单元测试

### v1.5.3

1. 功能标签不可用告警仅对正常状态节点生效
2. null qos 巡检仅对可用机房生效

### v1.5.2

1. 用 go-common log 替换 carbon log，支持 trace 方便排查问题
2. 用 go-common blademaster 替换 bee-go, 支持公司的 pprof 分析平台 方便排查问题
3. 非 Normal 状态的节点不再巡检 IP 冲突
4. 修复归因分析查询 clickhouse 失败问题
5. 去掉“恢复”通知

### v1.5.1

1. 机器功能标签状态异常归因分析

### v1.5.0

1. bban qos 拨测数据打印到日志

### v1.4.9

1. 更新 go.mod

### v1.4.8

1. bban idc,switch,node 打印到日志
2. idc 直播带宽为负时，发巡检告警

### v1.4.7

1. 调整 bvccdn 巡检任务时间，修复部分问题

### v1.4.6

1. 增加 bvccdn 巡检任务，修复部分问题

### v1.4.5

1. 修复时区问题
2. 修复聚合查询 changecube 失败问题
3. 修复删除 dsa path 超时问题
4. 修复查找 dependency 失败问题

### v1.4.0

1. 增加 bvccdn 巡检任务

### v1.3.4

1. 简化 bsql 解析 datacube

### v1.3.3

1. 聚合查询 CK
2. 删除 python 代码

### v1.2.3

1. 在本地开发环境，直接读写 uat 的 clickhouse, mysql, redis （支持本地开发调试）

### v1.2.2

1. dsa-path 聚合与展示

### v1.0.7

1. 解决 OOM 2. 降低请求 CK 数据库 qps, 满足数据库表迁移线上需求
   2.1 定时任务启动时间打散
   2.2 用队列实现 sql 异步执行，让 sql 执行请求的 qps 平滑

### v1.0.6

1. 使用 clickhouse 统一大表
2. ip 冲突告警增加 ip 地址展示

### v1.0.5

1. 增加告警群可配置功能

### v1.0.4

1. 适配 clickhouse

### v1.0.3

1. 增加配置文件动态获取
2. 增加带宽溢出阈值
3. 增加机房带宽浪费阈值
4. 增加 lan isp
5. 增加标签告警业务判断

### v1.0.2

1. 增加巡检配置动态开关功能
2. 更新 go.mod

### v1.0.1

1. 增加巡检功能
2. 添加流水线
3. go-common 升级到 1.45.5
