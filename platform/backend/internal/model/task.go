package model

import (
	"fmt"
	"time"
)

// 任务状态机：pending -> running -> completed / failed。
const (
	StatusPending   = "pending"
	StatusRunning   = "running"
	StatusCompleted = "completed"
	StatusFailed    = "failed"
)

// 双开关取值（与 tools/ch5_system_runner.py 的 argparse choices 逐项一致）。
const (
	DataBudgetNaive        = "naive"
	DataBudgetQuotaDeficit = "quota_deficit"
	MemberEngineOff        = "off"
	MemberEngineTabM4      = "tabm4"
)

// Task 是平台侧的任务记录。MetricsJSON 保存任务完成时对 result JSON 的快照，
// 便于结果文件被移走后仍能追溯；对外的权威读数仍以结果文件为准。
type Task struct {
	ID           uint       `gorm:"primaryKey" json:"id"`
	DataBudget   string     `gorm:"size:32;not null;index" json:"data_budget"`
	MemberEngine string     `gorm:"size:32;not null" json:"member_engine"`
	Status       string     `gorm:"size:16;not null;default:pending;index" json:"status"`
	CreatedAt    time.Time  `json:"created_at"`
	StartedAt    *time.Time `json:"started_at"`
	FinishedAt   *time.Time `json:"finished_at"`
	LogPath      string     `gorm:"size:512" json:"log_path"`
	MetricsJSON  string     `gorm:"type:longtext" json:"-"`
}

// TableName 固定表名，避免 GORM 复数化策略升级后静默改名。
func (Task) TableName() string { return "tasks" }

// ValidateSwitches 校验双开关枚举；错误信息直接面向 API 调用方。
func ValidateSwitches(dataBudget, memberEngine string) error {
	switch dataBudget {
	case DataBudgetNaive, DataBudgetQuotaDeficit:
	default:
		return fmt.Errorf("data_budget 取值必须是 %q 或 %q，收到 %q",
			DataBudgetNaive, DataBudgetQuotaDeficit, dataBudget)
	}
	switch memberEngine {
	case MemberEngineOff, MemberEngineTabM4:
	default:
		return fmt.Errorf("member_engine 取值必须是 %q 或 %q，收到 %q",
			MemberEngineOff, MemberEngineTabM4, memberEngine)
	}
	return nil
}

// CellName 返回双开关对应的四格名称。
// 该映射必须与 tools/ch5_system_runner.py 的 CELL_SPEC 逐项一致：
//
//	naive + off        -> naive
//	quota_deficit + off -> replay
//	naive + tabm4      -> naive_members
//	quota_deficit + tabm4 -> full
func CellName(dataBudget, memberEngine string) (string, error) {
	if err := ValidateSwitches(dataBudget, memberEngine); err != nil {
		return "", err
	}
	switch {
	case dataBudget == DataBudgetNaive && memberEngine == MemberEngineOff:
		return "naive", nil
	case dataBudget == DataBudgetQuotaDeficit && memberEngine == MemberEngineOff:
		return "replay", nil
	case dataBudget == DataBudgetNaive && memberEngine == MemberEngineTabM4:
		return "naive_members", nil
	case dataBudget == DataBudgetQuotaDeficit && memberEngine == MemberEngineTabM4:
		return "full", nil
	default:
		return "", fmt.Errorf("开关组合不在四格之内：data_budget=%q member_engine=%q",
			dataBudget, memberEngine)
	}
}
