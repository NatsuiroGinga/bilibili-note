package store

import (
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"sync"
	"time"

	"ch5platform/backend/internal/model"
)

// ErrNotFound 表示任务 ID 不存在；HTTP 层用 errors.Is 映射为 404。
var ErrNotFound = errors.New("任务不存在")

// Store 是任务生命周期的持久化抽象。
// MySQL 是唯一生产实现；Memory 仅供 -skip-db 的 API 接线开发验证。
type Store interface {
	CreateTask(dataBudget, memberEngine string, createdAt time.Time) (*model.Task, error)
	ListTasks() ([]model.Task, error)
	GetTask(id uint) (*model.Task, error)
	ClaimNextPending(startedAt time.Time, logPath func(uint) string) (*model.Task, error)
	MarkCompleted(id uint, metrics string, finishedAt time.Time) error
	MarkFailed(id uint, failure error, finishedAt time.Time) error
	RecoverInterrupted(finishedAt time.Time) (int64, error)
	Close() error
	Backend() string
}

func failureJSON(err error) string {
	payload, marshalErr := json.Marshal(map[string]string{"error": err.Error()})
	if marshalErr != nil {
		return `{"error":"任务失败，且错误信息序列化失败"}`
	}
	return string(payload)
}

// Memory 是 -skip-db 模式的进程内任务存储。它不执行任何训练子进程，
// 服务退出后数据即丢弃，禁止用于真实实验。
type Memory struct {
	mu     sync.Mutex
	tasks  map[uint]*model.Task
	nextID uint
}

// NewMemory 创建空的内存任务存储。
func NewMemory() *Memory {
	return &Memory{tasks: make(map[uint]*model.Task)}
}

func (m *Memory) Backend() string { return "memory" }

func (m *Memory) Close() error { return nil }

func (m *Memory) CreateTask(dataBudget, memberEngine string, createdAt time.Time) (*model.Task, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.nextID++
	task := &model.Task{
		ID:           m.nextID,
		DataBudget:   dataBudget,
		MemberEngine: memberEngine,
		Status:       model.StatusPending,
		CreatedAt:    createdAt,
	}
	stored := cloneTask(*task)
	m.tasks[task.ID] = &stored
	result := cloneTask(*task)
	return &result, nil
}

func (m *Memory) ListTasks() ([]model.Task, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	tasks := make([]model.Task, 0, len(m.tasks))
	for _, task := range m.tasks {
		tasks = append(tasks, cloneTask(*task))
	}
	sort.Slice(tasks, func(i, j int) bool { return tasks[i].ID > tasks[j].ID })
	return tasks, nil
}

func (m *Memory) GetTask(id uint) (*model.Task, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	task, ok := m.tasks[id]
	if !ok {
		return nil, fmt.Errorf("查询内存任务 %d: %w", id, ErrNotFound)
	}
	result := cloneTask(*task)
	return &result, nil
}

func (m *Memory) ClaimNextPending(startedAt time.Time, logPath func(uint) string) (*model.Task, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var oldest *model.Task
	for _, task := range m.tasks {
		if task.Status != model.StatusPending {
			continue
		}
		if oldest == nil || task.ID < oldest.ID {
			oldest = task
		}
	}
	if oldest == nil {
		return nil, nil
	}
	oldest.Status = model.StatusRunning
	oldest.StartedAt = timePtr(startedAt)
	oldest.LogPath = logPath(oldest.ID)
	result := cloneTask(*oldest)
	return &result, nil
}

func (m *Memory) MarkCompleted(id uint, metrics string, finishedAt time.Time) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	task, ok := m.tasks[id]
	if !ok {
		return fmt.Errorf("标记内存任务 %d 完成: %w", id, ErrNotFound)
	}
	task.Status = model.StatusCompleted
	task.FinishedAt = timePtr(finishedAt)
	task.MetricsJSON = metrics
	return nil
}

func (m *Memory) MarkFailed(id uint, failure error, finishedAt time.Time) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	task, ok := m.tasks[id]
	if !ok {
		return fmt.Errorf("标记内存任务 %d 失败: %w", id, ErrNotFound)
	}
	task.Status = model.StatusFailed
	task.FinishedAt = timePtr(finishedAt)
	task.MetricsJSON = failureJSON(failure)
	return nil
}

func (m *Memory) RecoverInterrupted(finishedAt time.Time) (int64, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var count int64
	for _, task := range m.tasks {
		if task.Status != model.StatusRunning {
			continue
		}
		task.Status = model.StatusFailed
		task.FinishedAt = timePtr(finishedAt)
		task.MetricsJSON = failureJSON(errors.New("服务重启时任务仍处于 running，已标记为 failed；请检查日志确认子进程状态"))
		count++
	}
	return count, nil
}

func cloneTask(task model.Task) model.Task {
	clone := task
	if task.StartedAt != nil {
		value := *task.StartedAt
		clone.StartedAt = &value
	}
	if task.FinishedAt != nil {
		value := *task.FinishedAt
		clone.FinishedAt = &value
	}
	return clone
}

func timePtr(value time.Time) *time.Time { return &value }
