package config

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// DefaultPythonBinary 是本机唯一实验环境的解释器（仓库 AGENTS.md 冻结）。
// 可用 -python 或 CH5_PYTHON 覆盖。
const DefaultPythonBinary = "/opt/miniconda3/envs/rwkv/bin/python"

// Config 保存平台运行配置。MySQLDSN 只来自环境变量 CH5_MYSQL_DSN，
// 不提供命令行参数，避免凭据进入 shell 历史与进程列表；任何日志都不得打印它。
type Config struct {
	Addr         string
	RepoRoot     string
	ProbeDir     string
	PythonBinary string
	RunnerScript string
	FrontendDist string
	CORSOrigins  []string
	MySQLDSN     string
	SkipDB       bool
	CheckDB      bool
	Debug        bool
	Smoke        bool
}

// DSNConfigured 只暴露“是否设置”，不泄露内容。
func (c Config) DSNConfigured() bool { return strings.TrimSpace(c.MySQLDSN) != "" }

// Load 解析命令行与环境变量，并执行路径与数据库配置的启动断言。
func Load(args []string) (Config, error) {
	fs := flag.NewFlagSet("ch5platform", flag.ContinueOnError)
	addr := fs.String("addr", envOr("CH5_ADDR", "127.0.0.1:8080"),
		"HTTP 监听地址（环境变量 CH5_ADDR）")
	repoRoot := fs.String("repo-root", os.Getenv("CH5_REPO_ROOT"),
		"仓库根目录；留空则从当前目录向上查找 platform/backend/go.mod（环境变量 CH5_REPO_ROOT）")
	probeDir := fs.String("probe-dir", os.Getenv("CH5_PROBE_DIR"),
		"训练内核目录；留空则为 <repo-root>/thesis/experiments/llm_probe（环境变量 CH5_PROBE_DIR）")
	pythonBinary := fs.String("python", envOr("CH5_PYTHON", DefaultPythonBinary),
		"Python 解释器路径（环境变量 CH5_PYTHON）")
	runnerScript := fs.String("runner", envOr("CH5_RUNNER", "tools/ch5_system_runner.py"),
		"训练内核脚本；相对路径以 probe-dir 为工作目录（环境变量 CH5_RUNNER）")
	frontendDist := fs.String("frontend-dist", os.Getenv("CH5_FRONTEND_DIST"),
		"前端构建产物目录；留空则为 <repo-root>/platform/frontend/dist（环境变量 CH5_FRONTEND_DIST）")
	corsOrigins := fs.String("cors-origins",
		envOr("CH5_CORS_ORIGINS",
			"http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"),
		"允许的 CORS 来源，逗号分隔；设为 * 允许全部（环境变量 CH5_CORS_ORIGINS）")
	skipDB := fs.Bool("skip-db", envBool("CH5_SKIP_DB"),
		"开发验证专用：跳过 MySQL，使用内存任务存储且不启动训练执行协程（环境变量 CH5_SKIP_DB=1）")
	checkDB := fs.Bool("check-db", false,
		"仅检查 CH5_MYSQL_DSN：连接、Ping、迁移任务表后退出，不启动服务")
	debug := fs.Bool("debug", false, "以 Gin debug 模式运行")
	smoke := fs.Bool("smoke", false,
		"接线冒烟：用同一 exec 路径运行 <python> --version 后退出，不启动服务、不创建任务")
	if err := fs.Parse(args); err != nil {
		return Config{}, err
	}
	if *skipDB && *checkDB {
		return Config{}, errors.New("-skip-db 与 -check-db 不能同时使用")
	}

	cfg := Config{
		Addr:         strings.TrimSpace(*addr),
		RepoRoot:     strings.TrimSpace(*repoRoot),
		ProbeDir:     strings.TrimSpace(*probeDir),
		PythonBinary: strings.TrimSpace(*pythonBinary),
		RunnerScript: strings.TrimSpace(*runnerScript),
		FrontendDist: strings.TrimSpace(*frontendDist),
		CORSOrigins:  splitCSV(*corsOrigins),
		MySQLDSN:     strings.TrimSpace(os.Getenv("CH5_MYSQL_DSN")),
		SkipDB:       *skipDB,
		CheckDB:      *checkDB,
		Debug:        *debug,
		Smoke:        *smoke,
	}
	if cfg.Addr == "" {
		return Config{}, errors.New("监听地址不能为空，请用 -addr 或 CH5_ADDR 指定")
	}
	if cfg.PythonBinary == "" {
		return Config{}, errors.New("Python 解释器不能为空，请用 -python 或 CH5_PYTHON 指定")
	}
	if cfg.RunnerScript == "" {
		return Config{}, errors.New("训练内核脚本路径不能为空，请用 -runner 或 CH5_RUNNER 指定")
	}

	if cfg.RepoRoot == "" {
		root, err := discoverRepoRoot()
		if err != nil {
			return Config{}, err
		}
		cfg.RepoRoot = root
	}
	absRoot, err := filepath.Abs(cfg.RepoRoot)
	if err != nil {
		return Config{}, fmt.Errorf("解析仓库根目录 %q: %w", cfg.RepoRoot, err)
	}
	cfg.RepoRoot = absRoot

	if cfg.ProbeDir == "" {
		cfg.ProbeDir = filepath.Join(cfg.RepoRoot, "thesis", "experiments", "llm_probe")
	}
	if cfg.FrontendDist == "" {
		cfg.FrontendDist = filepath.Join(cfg.RepoRoot, "platform", "frontend", "dist")
	}
	if cfg.ProbeDir, err = filepath.Abs(cfg.ProbeDir); err != nil {
		return Config{}, fmt.Errorf("解析训练内核目录 %q: %w", cfg.ProbeDir, err)
	}
	if cfg.FrontendDist, err = filepath.Abs(cfg.FrontendDist); err != nil {
		return Config{}, fmt.Errorf("解析前端产物目录 %q: %w", cfg.FrontendDist, err)
	}

	info, err := os.Stat(cfg.ProbeDir)
	if err != nil {
		return Config{}, fmt.Errorf("训练内核目录不可用 %q: %w", cfg.ProbeDir, err)
	}
	if !info.IsDir() {
		return Config{}, fmt.Errorf("训练内核目录不是目录：%q", cfg.ProbeDir)
	}

	// 数据库启动断言：非 smoke / 非 skip-db 时必须显式提供 DSN，不回退 SQLite。
	if !cfg.Smoke && !cfg.SkipDB && !cfg.DSNConfigured() {
		return Config{}, errors.New(
			"未设置环境变量 CH5_MYSQL_DSN，平台不使用 SQLite 回退。" +
				"请设置形如 '<user>:<password>@tcp(127.0.0.1:3306)/ch5platform?charset=utf8mb4&parseTime=True' 的 DSN；" +
				"仅做 API 接线开发验证时可用 -skip-db（内存存储，不启动训练执行协程）")
	}
	return cfg, nil
}

// discoverRepoRoot 从当前目录向上查找模块文件，兼容在仓库根或 platform/backend 下启动。
func discoverRepoRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("获取当前工作目录: %w", err)
	}
	for {
		candidate := filepath.Join(dir, "platform", "backend", "go.mod")
		if info, statErr := os.Stat(candidate); statErr == nil && !info.IsDir() {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return "", errors.New("从当前目录向上未找到 platform/backend/go.mod，请用 -repo-root 指定仓库根目录")
}

func envOr(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok && strings.TrimSpace(value) != "" {
		return value
	}
	return fallback
}

func envBool(key string) bool {
	switch strings.ToLower(strings.TrimSpace(os.Getenv(key))) {
	case "1", "true", "yes", "on":
		return true
	default:
		return false
	}
}

func splitCSV(raw string) []string {
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		if trimmed := strings.TrimSpace(part); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}
