package runner

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"ch5platform/backend/internal/model"
)

// RunDirRel 是训练内核产物目录，相对于 llm_probe 根目录。
const RunDirRel = "runs/diagnostics/ch5-system"

// Config 描述如何调用 Python 训练内核。
type Config struct {
	PythonBinary string
	ProbeDir     string
	RunnerScript string
}

// Spec 是一次训练子进程调用的完整描述。
type Spec struct {
	Cell       string
	ResultPath string
	Args       []string
}

// RunDir 返回绝对产物目录。
func (c Config) RunDir() string {
	return filepath.Join(c.ProbeDir, filepath.FromSlash(RunDirRel))
}

// TaskLogRel 返回任务日志相对 llm_probe 的路径，写入数据库 LogPath 字段。
func (c Config) TaskLogRel(id uint) string {
	return filepath.ToSlash(filepath.Join(filepath.FromSlash(RunDirRel), fmt.Sprintf("task_%d.log", id)))
}

// Spec 把双开关映射为内核命令行与结果文件路径。
func (c Config) Spec(dataBudget, memberEngine string) (Spec, error) {
	cell, err := model.CellName(dataBudget, memberEngine)
	if err != nil {
		return Spec{}, fmt.Errorf("解析双开关对应的四格: %w", err)
	}
	return Spec{
		Cell:       cell,
		ResultPath: filepath.Join(c.RunDir(), cell+"-result.json"),
		Args: []string{
			c.RunnerScript,
			"--data-budget", dataBudget,
			"--member-engine", memberEngine,
		},
	}, nil
}

// RunLogged 以子进程执行命令，把 stdout/stderr 汇总重定向到 logPath，返回进程退出码。
// 训练任务与 -smoke 接线验证共用这一条执行路径。
func RunLogged(ctx context.Context, binary string, args []string, dir, logPath string) (int, error) {
	if err := os.MkdirAll(filepath.Dir(logPath), 0o755); err != nil {
		return -1, fmt.Errorf("创建日志目录 %q: %w", filepath.Dir(logPath), err)
	}
	logFile, err := os.Create(logPath)
	if err != nil {
		return -1, fmt.Errorf("创建日志文件 %q: %w", logPath, err)
	}
	defer func() { _ = logFile.Close() }()

	// 只记录命令与工作目录，不记录环境变量（可能含数据根或凭据）。
	if _, err := fmt.Fprintf(logFile,
		"[platform] %s\n[platform] cwd=%s\n[platform] cmd=%s %s\n\n",
		time.Now().Format(time.RFC3339), dir, binary, strings.Join(args, " ")); err != nil {
		return -1, fmt.Errorf("写入日志头 %q: %w", logPath, err)
	}

	cmd := exec.CommandContext(ctx, binary, args...)
	cmd.Dir = dir
	cmd.Stdout = logFile
	cmd.Stderr = logFile
	if err := cmd.Start(); err != nil {
		return -1, fmt.Errorf("启动子进程 %q: %w", binary, err)
	}
	if err := cmd.Wait(); err != nil {
		var exitErr *exec.ExitError
		if errors.As(err, &exitErr) {
			return exitErr.ExitCode(), fmt.Errorf("子进程退出码 %d: %w", exitErr.ExitCode(), err)
		}
		return -1, fmt.Errorf("等待子进程 %q: %w", binary, err)
	}
	return 0, nil
}
