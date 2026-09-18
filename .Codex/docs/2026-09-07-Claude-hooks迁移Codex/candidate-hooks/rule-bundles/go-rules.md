【按需注入·Go 代码规范】本条规则因本次触碰 .go 文件注入，写/审 Go 代码必须遵守。

## 错误处理（层层包裹，顶层打印）
- 禁止裸 `return err`、禁止 `errors.New` 丢弃原始错误链；每层用 `fmt.Errorf("操作描述(入参): %w", err)` 包裹并补充本层业务上下文
- 中间层只返回错误、严禁打日志；日志统一在顶层（main/HTTP 中间件/拦截器）打印一次
- 哨兵错误用 `errors.Is` 判断，自定义错误类型用 `errors.As` 提取；包裹一律 `%w`（`%v` 会断链）

## Panic 防御
- GO-PANIC-001 类型断言必须 `val, ok := x.(T)` 双返回值并处理 !ok（测试代码或有 recover 除外）
- GO-PANIC-002 禁止忽略 error 后继续使用可能为空的指针/返回值
- GO-PANIC-003 硬编码索引访问切片/数组前必须检查长度（range 内部除外）
- GO-PANIC-004 goroutine 内使用外部指针前先判空或将值复制传入

## 并发与 race
- goroutine 必须用 WaitGroup/Mutex/channel 管理生命周期，禁止裸 go 不管；goroutine 内必须 recover 防 panic 崩进程
- GO-DATARACE-001 禁止无同步保护地在 goroutine 内写共享 map/slice/变量（用 mutex/sync.Map/atomic）
- GO-DATARACE-004 WaitGroup/Mutex 等同步原语必须指针传递，禁止值拷贝
- 带缓冲 channel 注意关闭时机，防死锁或向已关闭 channel 发送

## 数据库
- GO-DATABASE-002 禁止循环内单条 SQL（N+1），集合 >10 改 `WHERE id IN` 批量
- GO-DATABASE-003 IN 参数 >1000 必须分批（每批 500-1000）
- GO-DATABASE-006 禁止循环内开/提交事务，循环外一个大事务
- GO-DATABASE-007 大表 UPDATE 分批（每批 1000-5000），防长事务锁表

## 日志与可测试性
- 使用项目已有日志库，Error 级用 log.Error、业务关键节点 log.Warn；禁止生产残留 fmt.Println/log.Printf/调试输出
- 核心逻辑面向单测设计：不硬编码 DB/网络调用，依赖注入、小接口便于 mock

## 安全与风格
- 外部输入必须边界校验；日志禁打印密码/token/密钥；禁止残留 TODO/FIXME/DEBUG/临时注释
- 提交前 gofmt；业务常量用 const，路径/端口/超时读配置，禁止硬编码魔数；提交前清理无用导入与变量
