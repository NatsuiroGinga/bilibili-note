package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"ch5platform/backend/internal/model"
	"ch5platform/backend/internal/runner"
	"ch5platform/backend/internal/store"
)

const idlePoll = 5 * time.Second

// Worker 是唯一的训练执行协程：同一时刻最多一个训练子进程（MPS 约束）。
type Worker struct {
	store  store.Store
	runner runner.Config
	wake   chan struct{}
	done   chan struct{}
}

// New 创建工作协程；调用方随后必须启动 Run。
func New(st store.Store, rc runner.Config) *Worker {
	return &Worker{
		store:  st,
		runner: rc,
		wake:   make(chan struct{}, 1),
		done:   make(chan struct{}),
	}
}

// Enqueue 只是唤醒信号；权威队列是数据库中的 pending 任务，信号可合并、可丢失。
func (w *Worker) Enqueue() {
	select {
	case w.wake <- struct{}{}:
	default:
	}
}

// Done 在 Run 退出后关闭，供主进程优雅等待。
func (w *Worker) Done() <-chan struct{} { return w.done }

// Run 串行消费 pending 任务，直到 ctx 被取消。
func (w *Worker) Run(ctx context.Context) {
	defer close(w.done)
	for {
		if ctx.Err() != nil {
			return
		}
		task, err := w.store.ClaimNextPending(time.Now(), w.runner.TaskLogRel)
		if err != nil {
			log.Printf("[worker] 领取待执行任务失败：%v", err)
		} else if task != nil {
			w.executeSafely(ctx, task)
			continue
		}
		select {
		case <-ctx.Done():
			return
		case <-w.wake:
		case <-time.After(idlePoll):
		}
	}
}

// executeSafely 隔离单任务的 panic，避免一个异常读数拖垮整个队列。
func (w *Worker) executeSafely(ctx context.Context, task *model.Task) {
	defer func() {
		if recovered := recover(); recovered != nil {
			w.fail(task, w.logPath(task), fmt.Errorf("执行任务时发生 panic: %v", recovered))
		}
	}()
	w.execute(ctx, task)
}

func (w *Worker) execute(ctx context.Context, task *model.Task) {
	spec, err := w.runner.Spec(task.DataBudget, task.MemberEngine)
	if err != nil {
		w.fail(task, w.logPath(task), fmt.Errorf("解析任务配置: %w", err))
		return
	}
	logPath := w.logPath(task)
	startedAt := time.Now()

	exitCode, runErr := runner.RunLogged(
		ctx, w.runner.PythonBinary, spec.Args, w.runner.ProbeDir, logPath)
	finishedAt := time.Now()
	if runErr != nil {
		w.fail(task, logPath,
			fmt.Errorf("训练子进程失败（cell=%s exit=%d）: %w", spec.Cell, exitCode, runErr))
		return
	}

	stat, err := os.Stat(spec.ResultPath)
	if err != nil {
		w.fail(task, logPath,
			fmt.Errorf("子进程已退出但结果文件不可读 %q: %w", spec.ResultPath, err))
		return
	}
	// 防止读取上一轮留下的同名结果：文件必须在本次任务开始后被重写。
	if !stat.ModTime().After(startedAt) {
		w.fail(task, logPath, fmt.Errorf(
			"结果文件 %q 的修改时间 %s 不晚于任务开始时间 %s，拒绝使用可能陈旧的读数",
			spec.ResultPath,
			stat.ModTime().Format(time.RFC3339Nano),
			startedAt.Format(time.RFC3339Nano)))
		return
	}
	raw, err := os.ReadFile(spec.ResultPath)
	if err != nil {
		w.fail(task, logPath, fmt.Errorf("读取结果文件 %q: %w", spec.ResultPath, err))
		return
	}
	var head struct {
		Cell string `json:"cell"`
	}
	if err := json.Unmarshal(raw, &head); err != nil {
		w.fail(task, logPath, fmt.Errorf("解析结果文件 %q: %w", spec.ResultPath, err))
		return
	}
	if head.Cell != spec.Cell {
		w.fail(task, logPath, fmt.Errorf(
			"结果文件 %q 的 cell=%q 与任务期望 cell=%q 不一致",
			spec.ResultPath, head.Cell, spec.Cell))
		return
	}
	if err := w.store.MarkCompleted(task.ID, string(raw), finishedAt); err != nil {
		log.Printf("[worker] 任务 %d 已执行完成但写回完成状态失败：%v", task.ID, err)
		return
	}
	log.Printf("[worker] 任务 %d 完成：cell=%s 用时=%s",
		task.ID, spec.Cell, finishedAt.Sub(startedAt).Round(time.Second))
}

func (w *Worker) fail(task *model.Task, logPath string, failure error) {
	log.Printf("[worker] 任务 %d 失败：%v", task.ID, failure)
	if logPath != "" {
		file, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
		if err != nil {
			log.Printf("[worker] 追加失败原因到日志 %q 失败：%v", logPath, err)
		} else {
			if _, writeErr := fmt.Fprintf(file, "\n[platform] 任务失败：%s\n", failure.Error()); writeErr != nil {
				log.Printf("[worker] 写入失败原因到日志 %q 失败：%v", logPath, writeErr)
			}
			if closeErr := file.Close(); closeErr != nil {
				log.Printf("[worker] 关闭日志文件 %q 失败：%v", logPath, closeErr)
			}
		}
	}
	if err := w.store.MarkFailed(task.ID, failure, time.Now()); err != nil {
		log.Printf("[worker] 写入任务 %d 失败状态时出错：%v", task.ID, err)
	}
}

func (w *Worker) logPath(task *model.Task) string {
	relative := task.LogPath
	if relative == "" {
		relative = w.runner.TaskLogRel(task.ID)
	}
	return filepath.Join(w.runner.ProbeDir, filepath.FromSlash(relative))
}
