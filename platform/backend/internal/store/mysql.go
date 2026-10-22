package store

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/go-sql-driver/mysql"
	gormmysql "gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"ch5platform/backend/internal/model"
)

// MySQL 是唯一生产存储实现。
// DSN 只从环境变量 CH5_MYSQL_DSN 读取；本类型及调用方都不得打印 DSN。
type MySQL struct {
	db *gorm.DB
}

// OpenMySQL 建立连接、执行 Ping 并迁移任务表。
// 失败时明确提示检查 CH5_MYSQL_DSN，不回退 SQLite 或其他存储。
func OpenMySQL(dsn string) (*MySQL, error) {
	if strings.TrimSpace(dsn) == "" {
		return nil, errors.New(
			"CH5_MYSQL_DSN 为空；平台只支持 MySQL，不回退 SQLite。" +
				"请设置环境变量 CH5_MYSQL_DSN（不要写入仓库或命令行参数）")
	}
	parsed, err := mysql.ParseDSN(dsn)
	if err != nil {
		return nil, fmt.Errorf("CH5_MYSQL_DSN 格式无效（不回显 DSN，避免泄露凭据）: %w", err)
	}
	// GORM 读写 time.Time 需要 parseTime=True；在内存中补齐，不改变凭据来源。
	parsed.ParseTime = true

	db, err := gorm.Open(gormmysql.Open(parsed.FormatDSN()), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn),
	})
	if err != nil {
		return nil, fmt.Errorf("连接 MySQL 失败，请检查 CH5_MYSQL_DSN 与数据库服务状态: %w", err)
	}
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("获取 MySQL 连接池: %w", err)
	}
	sqlDB.SetMaxOpenConns(10)
	sqlDB.SetMaxIdleConns(5)
	sqlDB.SetConnMaxLifetime(30 * time.Minute)

	pingCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := sqlDB.PingContext(pingCtx); err != nil {
		closeErr := sqlDB.Close()
		if closeErr != nil {
			return nil, fmt.Errorf("MySQL Ping 失败: %w（同时关闭连接池失败: %v）", err, closeErr)
		}
		return nil, fmt.Errorf("MySQL Ping 失败，请检查 CH5_MYSQL_DSN 与数据库服务状态: %w", err)
	}
	if err := db.AutoMigrate(&model.Task{}); err != nil {
		closeErr := sqlDB.Close()
		if closeErr != nil {
			return nil, fmt.Errorf("迁移任务表失败: %w（同时关闭连接池失败: %v）", err, closeErr)
		}
		return nil, fmt.Errorf("迁移任务表失败: %w", err)
	}
	return &MySQL{db: db}, nil
}

func (m *MySQL) Backend() string { return "mysql" }

func (m *MySQL) Close() error {
	sqlDB, err := m.db.DB()
	if err != nil {
		return fmt.Errorf("获取 MySQL 连接池用于关闭: %w", err)
	}
	if err := sqlDB.Close(); err != nil {
		return fmt.Errorf("关闭 MySQL 连接池: %w", err)
	}
	return nil
}

func (m *MySQL) CreateTask(dataBudget, memberEngine string, createdAt time.Time) (*model.Task, error) {
	task := &model.Task{
		DataBudget:   dataBudget,
		MemberEngine: memberEngine,
		Status:       model.StatusPending,
		CreatedAt:    createdAt,
	}
	if err := m.db.Create(task).Error; err != nil {
		return nil, fmt.Errorf("写入任务（data_budget=%q member_engine=%q）: %w",
			dataBudget, memberEngine, err)
	}
	return task, nil
}

func (m *MySQL) ListTasks() ([]model.Task, error) {
	tasks := make([]model.Task, 0)
	if err := m.db.Order("id DESC").Find(&tasks).Error; err != nil {
		return nil, fmt.Errorf("查询任务列表: %w", err)
	}
	return tasks, nil
}

func (m *MySQL) GetTask(id uint) (*model.Task, error) {
	var task model.Task
	err := m.db.First(&task, id).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, fmt.Errorf("查询任务 %d: %w", id, ErrNotFound)
	}
	if err != nil {
		return nil, fmt.Errorf("查询任务 %d: %w", id, err)
	}
	return &task, nil
}

func (m *MySQL) ClaimNextPending(startedAt time.Time, logPath func(uint) string) (*model.Task, error) {
	var task model.Task
	err := m.db.Where("status = ?", model.StatusPending).Order("id ASC").First(&task).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("查询待执行任务: %w", err)
	}
	relativeLog := logPath(task.ID)
	result := m.db.Model(&model.Task{}).
		Where("id = ? AND status = ?", task.ID, model.StatusPending).
		Updates(map[string]any{
			"status":     model.StatusRunning,
			"started_at": startedAt,
			"log_path":   relativeLog,
		})
	if result.Error != nil {
		return nil, fmt.Errorf("领取任务 %d: %w", task.ID, result.Error)
	}
	if result.RowsAffected == 0 {
		// 单工作协程下不应发生；返回 nil 让工作协程重新轮询。
		return nil, nil
	}
	task.Status = model.StatusRunning
	task.StartedAt = &startedAt
	task.LogPath = relativeLog
	return &task, nil
}

func (m *MySQL) MarkCompleted(id uint, metrics string, finishedAt time.Time) error {
	result := m.db.Model(&model.Task{}).Where("id = ?", id).Updates(map[string]any{
		"status":       model.StatusCompleted,
		"finished_at":  finishedAt,
		"metrics_json": metrics,
	})
	if result.Error != nil {
		return fmt.Errorf("标记任务 %d 完成: %w", id, result.Error)
	}
	if result.RowsAffected == 0 {
		return fmt.Errorf("标记任务 %d 完成: %w", id, ErrNotFound)
	}
	return nil
}

func (m *MySQL) MarkFailed(id uint, failure error, finishedAt time.Time) error {
	result := m.db.Model(&model.Task{}).Where("id = ?", id).Updates(map[string]any{
		"status":       model.StatusFailed,
		"finished_at":  finishedAt,
		"metrics_json": failureJSON(failure),
	})
	if result.Error != nil {
		return fmt.Errorf("标记任务 %d 失败: %w", id, result.Error)
	}
	if result.RowsAffected == 0 {
		return fmt.Errorf("标记任务 %d 失败: %w", id, ErrNotFound)
	}
	return nil
}

// RecoverInterrupted 在进程启动时把遗留 running 任务标记为 failed。
// 这防止服务崩溃或强制退出后任务永远停在 running；单实例部署前提写进 README。
func (m *MySQL) RecoverInterrupted(finishedAt time.Time) (int64, error) {
	payload := failureJSON(errors.New(
		"服务重启时任务仍处于 running，已标记为 failed；请检查日志确认子进程是否仍在运行"))
	result := m.db.Model(&model.Task{}).Where("status = ?", model.StatusRunning).Updates(map[string]any{
		"status":       model.StatusFailed,
		"finished_at":  finishedAt,
		"metrics_json": payload,
	})
	if result.Error != nil {
		return 0, fmt.Errorf("恢复中断任务: %w", result.Error)
	}
	return result.RowsAffected, nil
}
