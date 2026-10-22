package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"ch5platform/backend/internal/config"
	"ch5platform/backend/internal/runner"
	"ch5platform/backend/internal/server"
	"ch5platform/backend/internal/store"
	"ch5platform/backend/internal/worker"
)

func main() {
	cfg, err := config.Load(os.Args[1:])
	if err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return
		}
		fmt.Fprintf(os.Stderr, "配置错误：%v\n", err)
		os.Exit(2)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	switch {
	case cfg.Smoke:
		if err := runSmoke(ctx, cfg); err != nil {
			log.Printf("[smoke] 失败：%v", err)
			os.Exit(1)
		}
	case cfg.CheckDB:
		if err := runCheckDB(cfg); err != nil {
			log.Printf("[check-db] 失败：%v", err)
			os.Exit(1)
		}
	default:
		if err := run(ctx, cfg); err != nil {
			log.Printf("服务退出：%v", err)
			os.Exit(1)
		}
	}
}

// runSmoke 用与训练任务相同的 exec 路径运行 <python> --version。
// 这是接线验证，不是训练；不连接数据库、不创建任务。
func runSmoke(ctx context.Context, cfg config.Config) error {
	tempDir, err := os.MkdirTemp("", "ch5-platform-smoke-")
	if err != nil {
		return fmt.Errorf("创建冒烟临时目录: %w", err)
	}
	defer func() {
		if err := os.RemoveAll(tempDir); err != nil {
			log.Printf("[smoke] 清理临时目录 %q 失败：%v", tempDir, err)
		}
	}()
	logPath := filepath.Join(tempDir, "smoke.log")
	exitCode, runErr := runner.RunLogged(
		ctx, cfg.PythonBinary, []string{"--version"}, cfg.ProbeDir, logPath)
	output, readErr := os.ReadFile(logPath)
	if readErr != nil {
		return fmt.Errorf("读取冒烟日志 %q: %w", logPath, readErr)
	}
	fmt.Printf("[smoke] 接线验证（非训练）：%s --version，cwd=%s，exit=%d\n",
		cfg.PythonBinary, cfg.ProbeDir, exitCode)
	fmt.Print(string(output))
	if runErr != nil {
		return fmt.Errorf("接线冒烟命令失败: %w", runErr)
	}
	return nil
}

// runCheckDB 只验证 CH5_MYSQL_DSN 可连接且任务表可迁移，然后退出。
// 不打印 DSN，也不启动 HTTP 服务或训练协程。
func runCheckDB(cfg config.Config) error {
	st, err := store.OpenMySQL(cfg.MySQLDSN)
	if err != nil {
		return err
	}
	if err := st.Close(); err != nil {
		return err
	}
	fmt.Println("[check-db] MySQL 连线验证通过：连接、Ping 与 tasks 表迁移均成功。")
	return nil
}

func run(ctx context.Context, cfg config.Config) error {
	st, err := openStore(cfg)
	if err != nil {
		return fmt.Errorf("数据库启动检查失败: %w", err)
	}
	defer func() {
		if err := st.Close(); err != nil {
			log.Printf("[shutdown] 关闭存储失败：%v", err)
		}
	}()

	recovered, err := st.RecoverInterrupted(time.Now().UTC())
	if err != nil {
		return fmt.Errorf("恢复中断任务: %w", err)
	}
	if recovered > 0 {
		log.Printf("[startup] 已将 %d 个中断的 running 任务标记为 failed", recovered)
	}

	runCtx, cancelRun := context.WithCancel(ctx)
	defer cancelRun()

	runnerCfg := runner.Config{
		PythonBinary: cfg.PythonBinary,
		ProbeDir:     cfg.ProbeDir,
		RunnerScript: cfg.RunnerScript,
	}
	var w *worker.Worker
	enqueue := func() {}
	if cfg.SkipDB {
		log.Printf("[startup] 警告：-skip-db 开发模式，使用内存任务存储；" +
			"不连接 MySQL，也不启动训练执行协程（不会产生任何训练子进程）")
	} else {
		if _, statErr := os.Stat(filepath.Join(cfg.ProbeDir, cfg.RunnerScript)); statErr != nil {
			log.Printf("[startup] 警告：训练内核脚本当前不可访问，提交任务会在执行时失败：%v", statErr)
		}
		w = worker.New(st, runnerCfg)
		go w.Run(runCtx)
		enqueue = w.Enqueue
	}

	httpServer := &http.Server{
		Addr:              cfg.Addr,
		Handler:           server.NewRouter(cfg, st, enqueue),
		ReadHeaderTimeout: 10 * time.Second,
	}
	serverErr := make(chan error, 1)
	go func() {
		log.Printf("[startup] 服务监听 %s；存储=%s；训练内核目录=%s；产物目录=%s",
			cfg.Addr, st.Backend(), cfg.ProbeDir, runnerCfg.RunDir())
		if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serverErr <- fmt.Errorf("HTTP 服务监听 %q: %w", cfg.Addr, err)
		}
	}()

	var serveErr error
	select {
	case <-ctx.Done():
		log.Printf("[shutdown] 收到退出信号")
	case serveErr = <-serverErr:
		log.Printf("[shutdown] %v", serveErr)
	}
	cancelRun()

	shutdownCtx, cancelShutdown := context.WithTimeout(context.Background(), 10*time.Second)
	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("[shutdown] 关闭 HTTP 服务失败：%v", err)
	}
	cancelShutdown()

	if w != nil {
		select {
		case <-w.Done():
		case <-time.After(10 * time.Second):
			log.Printf("[shutdown] 等待训练执行协程退出超时")
		}
	}
	return serveErr
}

func openStore(cfg config.Config) (store.Store, error) {
	if cfg.SkipDB {
		return store.NewMemory(), nil
	}
	return store.OpenMySQL(cfg.MySQLDSN)
}
