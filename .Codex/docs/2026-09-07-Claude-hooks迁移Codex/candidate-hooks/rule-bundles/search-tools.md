【按需注入·搜索工具规范】本条规则被 hook 检测到搜索行为时注入，仅约束本次相关动作。

代码搜索一律使用 ripgrep（rg），文件遍历一律使用 fd，禁止传统 grep 与内置搜索工具：
- 基础：`rg "关键词"`（自动尊重 .gitignore/.claudeignore）
- Go 代码：`rg "关键词" --type go`；文件名：`fd 关键词`；列 Go 文件：`fd -e go`
- 常用场景：函数定义 `rg "func.*名称" --type go`；TODO `rg "TODO|FIXME" --type go`；结构体 `rg "type.*struct" --type go`
- 不搜 vendor/、bin/、pkg/、.git/；不搜 .env、*.pem、config.yaml 等敏感文件
- 结果超过 20 条时先返回前 10 条并询问是否需要更多
