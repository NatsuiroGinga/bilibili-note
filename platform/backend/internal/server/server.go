package server

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"ch5platform/backend/internal/config"
	"ch5platform/backend/internal/model"
	"ch5platform/backend/internal/runner"
	"ch5platform/backend/internal/store"
)

const (
	defaultTailLines = 200
	maxTailLines     = 5000
	maxTailBytes     = 4 << 20
	maxRequestBody   = 1 << 20
)

type handlers struct {
	cfg     config.Config
	store   store.Store
	enqueue func()
}

type taskView struct {
	model.Task
	Cell    string          `json:"cell"`
	Metrics json.RawMessage `json:"metrics,omitempty"`
}

// NewRouter 注册 /api 路由、CORS 与前端静态托管（dist 存在时启用）。
func NewRouter(cfg config.Config, st store.Store, enqueue func()) *gin.Engine {
	if !cfg.Debug {
		gin.SetMode(gin.ReleaseMode)
	}
	if enqueue == nil {
		enqueue = func() {}
	}
	h := &handlers{cfg: cfg, store: st, enqueue: enqueue}

	router := gin.New()
	router.Use(gin.Logger(), gin.Recovery(), corsMiddleware(cfg.CORSOrigins))

	api := router.Group("/api")
	{
		api.GET("/health", h.health)
		api.POST("/tasks", h.createTask)
		api.GET("/tasks", h.listTasks)
		api.GET("/tasks/:id", h.getTask)
		api.GET("/tasks/:id/log", h.getLog)
		api.GET("/tasks/:id/results", h.getResults)
		api.GET("/comparison", h.getComparison)
	}
	h.attachFrontend(router)
	return router
}

func (h *handlers) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"backend": h.store.Backend(),
		"time":    time.Now().UTC(),
	})
}

func (h *handlers) createTask(c *gin.Context) {
	c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, maxRequestBody)
	var request struct {
		DataBudget   string `json:"data_budget"`
		MemberEngine string `json:"member_engine"`
	}
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": fmt.Sprintf("请求体必须是合法 JSON，且包含 data_budget 与 member_engine：%v", err),
		})
		return
	}
	request.DataBudget = strings.TrimSpace(request.DataBudget)
	request.MemberEngine = strings.TrimSpace(request.MemberEngine)
	if err := model.ValidateSwitches(request.DataBudget, request.MemberEngine); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	task, err := h.store.CreateTask(request.DataBudget, request.MemberEngine, time.Now().UTC())
	if err != nil {
		h.serverError(c, "创建任务", err)
		return
	}
	h.enqueue()
	c.JSON(http.StatusCreated, makeTaskView(*task, false))
}

func (h *handlers) listTasks(c *gin.Context) {
	tasks, err := h.store.ListTasks()
	if err != nil {
		h.serverError(c, "查询任务列表", err)
		return
	}
	views := make([]taskView, 0, len(tasks))
	for _, task := range tasks {
		views = append(views, makeTaskView(task, false))
	}
	c.JSON(http.StatusOK, views)
}

func (h *handlers) getTask(c *gin.Context) {
	task, ok := h.taskOr404(c)
	if !ok {
		return
	}
	c.JSON(http.StatusOK, makeTaskView(*task, true))
}

func (h *handlers) getLog(c *gin.Context) {
	task, ok := h.taskOr404(c)
	if !ok {
		return
	}
	wanted, ok := parseTailLines(c)
	if !ok {
		return
	}
	if task.LogPath == "" {
		c.JSON(http.StatusOK, gin.H{
			"task_id":         task.ID,
			"log_path":        "",
			"exists":          false,
			"requested_lines": wanted,
			"returned_lines":  0,
			"lines":           []string{},
		})
		return
	}
	logPath := filepath.Join(h.cfg.ProbeDir, filepath.FromSlash(task.LogPath))
	lines, err := tailLines(logPath, wanted)
	if errors.Is(err, os.ErrNotExist) {
		c.JSON(http.StatusOK, gin.H{
			"task_id":         task.ID,
			"log_path":        task.LogPath,
			"exists":          false,
			"requested_lines": wanted,
			"returned_lines":  0,
			"lines":           []string{},
		})
		return
	}
	if err != nil {
		h.serverError(c, "读取任务日志", err)
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"task_id":         task.ID,
		"log_path":        task.LogPath,
		"exists":          true,
		"requested_lines": wanted,
		"returned_lines":  len(lines),
		"lines":           lines,
	})
}

func (h *handlers) getResults(c *gin.Context) {
	task, ok := h.taskOr404(c)
	if !ok {
		return
	}
	cell, err := model.CellName(task.DataBudget, task.MemberEngine)
	if err != nil {
		h.serverError(c, "解析任务对应的四格", err)
		return
	}
	switch task.Status {
	case model.StatusCompleted:
		// 同一 cell 的结果文件会被后续运行覆盖，优先返回本任务完成时的 JSON 快照。
		if task.MetricsJSON != "" && json.Valid([]byte(task.MetricsJSON)) {
			c.Data(http.StatusOK, "application/json; charset=utf-8", []byte(task.MetricsJSON))
			return
		}
	case model.StatusFailed:
		c.JSON(http.StatusConflict, gin.H{
			"error": fmt.Sprintf("任务 %d 已失败，无可用结果：%s", task.ID, failureMessage(task.MetricsJSON)),
			"cell":  cell,
		})
		return
	default:
		c.JSON(http.StatusConflict, gin.H{
			"error": fmt.Sprintf("任务 %d 尚未完成（状态：%s），结果尚未生成", task.ID, task.Status),
			"cell":  cell,
		})
		return
	}
	// 仅当历史任务的快照缺失时，才回退读取当前 cell 结果文件。
	relative := filepath.ToSlash(filepath.Join(runner.RunDirRel, cell+"-result.json"))
	resultPath := filepath.Join(h.cfg.ProbeDir, filepath.FromSlash(relative))
	raw, err := os.ReadFile(resultPath)
	if errors.Is(err, os.ErrNotExist) {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("结果文件尚不存在：%s（任务状态：%s）", relative, task.Status),
		})
		return
	}
	if err != nil {
		h.serverError(c, "读取结果文件 "+relative, err)
		return
	}
	c.Data(http.StatusOK, "application/json; charset=utf-8", raw)
}

func (h *handlers) getComparison(c *gin.Context) {
	relative := filepath.ToSlash(filepath.Join(runner.RunDirRel, "system-comparison.json"))
	comparisonPath := filepath.Join(h.cfg.ProbeDir, filepath.FromSlash(relative))
	raw, err := os.ReadFile(comparisonPath)
	if errors.Is(err, os.ErrNotExist) {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("系统对比文件尚不存在：%s（四格尚未全部产生结果）", relative),
		})
		return
	}
	if err != nil {
		h.serverError(c, "读取系统对比文件 "+relative, err)
		return
	}
	c.Data(http.StatusOK, "application/json; charset=utf-8", raw)
}

func (h *handlers) taskOr404(c *gin.Context) (*model.Task, bool) {
	id, ok := parseTaskID(c)
	if !ok {
		return nil, false
	}
	task, err := h.store.GetTask(id)
	if errors.Is(err, store.ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("任务 %d 不存在", id)})
		return nil, false
	}
	if err != nil {
		h.serverError(c, "查询任务", err)
		return nil, false
	}
	return task, true
}

func (h *handlers) serverError(c *gin.Context, action string, err error) {
	log.Printf("[http] %s失败：%v", action, err)
	c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("%s失败：%v", action, err)})
}

func failureMessage(metricsJSON string) string {
	var payload struct {
		Error string `json:"error"`
	}
	if err := json.Unmarshal([]byte(metricsJSON), &payload); err == nil && payload.Error != "" {
		return payload.Error
	}
	return "未记录失败原因，请查看任务日志"
}

func makeTaskView(task model.Task, includeMetrics bool) taskView {
	cell, err := model.CellName(task.DataBudget, task.MemberEngine)
	if err != nil {
		cell = ""
	}
	view := taskView{Task: task, Cell: cell}
	if includeMetrics && task.MetricsJSON != "" && json.Valid([]byte(task.MetricsJSON)) {
		view.Metrics = json.RawMessage(task.MetricsJSON)
	}
	return view
}

func parseTaskID(c *gin.Context) (uint, bool) {
	raw := c.Param("id")
	value, err := strconv.ParseUint(raw, 10, 0)
	if err != nil || value == 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": fmt.Sprintf("任务 ID 必须是正整数，收到 %q", raw),
		})
		return 0, false
	}
	return uint(value), true
}

func parseTailLines(c *gin.Context) (int, bool) {
	raw := c.Query("lines")
	if raw == "" {
		return defaultTailLines, true
	}
	value, err := strconv.Atoi(raw)
	if err != nil || value <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": fmt.Sprintf("lines 必须是正整数，收到 %q", raw),
		})
		return 0, false
	}
	if value > maxTailLines {
		value = maxTailLines
	}
	return value, true
}

// tailLines 读取文件末尾最多 maxTailBytes 字节，返回最后 n 行。
func tailLines(filePath string, n int) ([]string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("打开日志文件 %q: %w", filePath, err)
	}
	defer func() { _ = file.Close() }()

	info, err := file.Stat()
	if err != nil {
		return nil, fmt.Errorf("读取日志文件信息 %q: %w", filePath, err)
	}
	size := info.Size()
	start := int64(0)
	if size > maxTailBytes {
		start = size - maxTailBytes
	}
	if _, err := file.Seek(start, io.SeekStart); err != nil {
		return nil, fmt.Errorf("定位日志文件 %q: %w", filePath, err)
	}
	data, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("读取日志文件 %q: %w", filePath, err)
	}
	text := string(data)
	if start > 0 {
		// 丢弃被截断的首行。
		if index := strings.IndexByte(text, '\n'); index >= 0 {
			text = text[index+1:]
		}
	}
	text = strings.TrimRight(text, "\n")
	if text == "" {
		return []string{}, nil
	}
	lines := strings.Split(text, "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return lines, nil
}

func corsMiddleware(origins []string) gin.HandlerFunc {
	allowed := make(map[string]struct{}, len(origins))
	allowAll := false
	for _, origin := range origins {
		if origin == "*" {
			allowAll = true
		}
		allowed[origin] = struct{}{}
	}
	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")
		permitted := allowAll
		if origin != "" && !permitted {
			_, permitted = allowed[origin]
		}
		if origin != "" && permitted {
			if allowAll {
				c.Header("Access-Control-Allow-Origin", "*")
			} else {
				c.Header("Access-Control-Allow-Origin", origin)
				c.Header("Vary", "Origin")
			}
			c.Header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			c.Header("Access-Control-Allow-Headers", "Content-Type")
			c.Header("Access-Control-Max-Age", "600")
		}
		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}

// attachFrontend 托管 platform/frontend/dist；SPA 的未知路径回退到 index.html。
func (h *handlers) attachFrontend(router *gin.Engine) {
	dist := h.cfg.FrontendDist
	indexPath := filepath.Join(dist, "index.html")
	info, err := os.Stat(indexPath)
	if err != nil || info.IsDir() {
		log.Printf("[server] 未找到前端构建产物 %q，静态托管未启用", indexPath)
		router.NoRoute(func(c *gin.Context) {
			if isAPIPath(c.Request.URL.Path) {
				c.JSON(http.StatusNotFound, gin.H{"error": "API 路由不存在"})
				return
			}
			c.JSON(http.StatusNotFound, gin.H{
				"error": "前端构建产物尚未生成，请先构建 platform/frontend",
			})
		})
		return
	}
	log.Printf("[server] 前端静态托管已启用：%s", dist)
	router.NoRoute(func(c *gin.Context) {
		if isAPIPath(c.Request.URL.Path) {
			c.JSON(http.StatusNotFound, gin.H{"error": "API 路由不存在"})
			return
		}
		cleaned := path.Clean("/" + c.Request.URL.Path)
		filePath := filepath.Join(dist, filepath.FromSlash(cleaned))
		if fileInfo, statErr := os.Stat(filePath); statErr == nil && !fileInfo.IsDir() {
			c.File(filePath)
			return
		}
		c.File(indexPath)
	})
}

func isAPIPath(requestPath string) bool {
	return requestPath == "/api" || strings.HasPrefix(requestPath, "/api/")
}
