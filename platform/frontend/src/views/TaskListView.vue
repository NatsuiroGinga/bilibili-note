<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listTasks, loadArtifactManifest, loadComparisonSnapshot } from '../api'
import { cellMeta, fmtClock, fmtDateTime, fmtF1, fmtWall } from '../format'
import { markPageReady, resetPageReady } from '../ready'
import CellBadge from '../components/CellBadge.vue'
import StatusTag from '../components/StatusTag.vue'

const router = useRouter()
const tasks = ref([])
const comparison = ref(null)
const manifest = ref(null)
const lastRefresh = ref(Date.now())
const error = ref('')
let timer = null

const counts = computed(() => {
  const result = { total: tasks.value.length, pending: 0, running: 0, completed: 0, failed: 0 }
  for (const task of tasks.value) {
    if (result[task.status] !== undefined) result[task.status] += 1
  }
  return result
})

const archivedRows = computed(() => {
  const cells = comparison.value?.cells || {}
  const order = ['naive', 'naive_members', 'replay', 'full']
  return order
    .filter((cell) => cells[cell])
    .map((cell) => ({
      cell,
      meta: cellMeta(cell),
      ...cells[cell],
    }))
})

const missingRows = computed(() => comparison.value?.missing_cells || [])

function taskDuration(task) {
  if (task.started_at && task.finished_at) {
    const delta = (new Date(task.finished_at) - new Date(task.started_at)) / 1000
    return Number.isFinite(delta) && delta >= 0 ? delta : null
  }
  if (task.started_at && task.status === 'running') {
    const delta = (lastRefresh.value - new Date(task.started_at).getTime()) / 1000
    return Number.isFinite(delta) && delta >= 0 ? delta : null
  }
  return null
}

async function refresh() {
  try {
    tasks.value = await listTasks()
    error.value = ''
  } catch (err) {
    error.value = err.message
  } finally {
    lastRefresh.value = Date.now()
  }
}

async function loadStatic() {
  const results = await Promise.allSettled([loadComparisonSnapshot(), loadArtifactManifest()])
  if (results[0].status === 'fulfilled') comparison.value = results[0].value.data
  if (results[1].status === 'fulfilled') manifest.value = results[1].value
}

function openTask(task) {
  router.push(`/tasks/${task.id}`)
}

function openCell(cell) {
  router.push(`/results/${cell}`)
}

onMounted(async () => {
  resetPageReady()
  await Promise.all([refresh(), loadStatic()])
  timer = window.setInterval(refresh, 5000)
  markPageReady(700)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h1 class="page-title">任务列表与运行状态</h1>
        <div class="page-sub">
          平台任务写入 MySQL 后由单工作协程串行执行；状态机为 pending → running → completed / failed。
          列表每 5 秒自动刷新。
        </div>
      </div>
      <div class="page-head-right">
        <span class="pill" :class="error ? 'warn' : 'ok'">
          <span class="dot" :class="{ warn: error }"></span>
          {{ error ? '刷新失败' : '自动刷新 · 每 5 秒' }}
        </span>
        <span class="muted">最近刷新 {{ fmtClock(lastRefresh) }}</span>
      </div>
    </div>

    <div class="kpi-grid five">
      <div class="kpi muted-accent">
        <div class="kpi-label">任务总数</div>
        <div class="kpi-value">{{ counts.total }}</div>
        <div class="kpi-foot">MySQL 任务表</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">排队中</div>
        <div class="kpi-value">{{ counts.pending }}</div>
        <div class="kpi-foot">pending</div>
      </div>
      <div class="kpi warn">
        <div class="kpi-label">运行中</div>
        <div class="kpi-value">{{ counts.running }}</div>
        <div class="kpi-foot">running · MPS 串行</div>
      </div>
      <div class="kpi ok">
        <div class="kpi-label">已完成</div>
        <div class="kpi-value">{{ counts.completed }}</div>
        <div class="kpi-foot">completed</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">失败</div>
        <div class="kpi-value">{{ counts.failed }}</div>
        <div class="kpi-foot">failed</div>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div class="card-title">平台任务<small>经 Go 后端 exec 调用训练内核</small></div>
        <span class="pill info">GET /api/tasks</span>
      </div>
      <div class="card-body tight">
        <el-table :data="tasks" size="small" style="width: 100%" empty-text="暂无平台任务">
          <el-table-column prop="id" label="ID" width="72">
            <template #default="{ row }">
              <span class="mono strong">#{{ row.id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="配置" min-width="215">
            <template #default="{ row }">
              <div class="row gap-8 nowrap">
                <span class="pill info">{{ row.data_budget }}</span>
                <span class="pill" :class="row.member_engine === 'tabm4' ? 'ok' : ''">
                  {{ row.member_engine }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="四格" width="132">
            <template #default="{ row }"><CellBadge :cell="row.cell" /></template>
          </el-table-column>
          <el-table-column label="状态" width="96">
            <template #default="{ row }"><StatusTag :status="row.status" /></template>
          </el-table-column>
          <el-table-column label="提交时间" width="160">
            <template #default="{ row }"><span class="mono small">{{ fmtDateTime(row.created_at) }}</span></template>
          </el-table-column>
          <el-table-column label="开始时间" width="160">
            <template #default="{ row }"><span class="mono small">{{ fmtDateTime(row.started_at) }}</span></template>
          </el-table-column>
          <el-table-column label="完成时间" width="160">
            <template #default="{ row }"><span class="mono small">{{ fmtDateTime(row.finished_at) }}</span></template>
          </el-table-column>
          <el-table-column label="耗时" width="105">
            <template #default="{ row }">
              <span class="mono">{{ fmtWall(taskDuration(row)) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                :disabled="row.status !== 'completed'"
                @click="openTask(row)"
              >
                查看结果
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="card" style="margin-top: 14px">
      <div class="card-head">
        <div class="card-title">已归档四格制品<small>CLI 直接运行收据 · 构建期快照</small></div>
        <span class="pill">{{ comparison?.completed_cells?.length || 0 }} / 4 格完成</span>
      </div>
      <div class="card-body tight">
        <el-table :data="archivedRows" size="small" style="width: 100%" empty-text="暂无归档制品">
          <el-table-column label="四格" width="150">
            <template #default="{ row }"><CellBadge :cell="row.cell" /></template>
          </el-table-column>
          <el-table-column label="配置" min-width="200">
            <template #default="{ row }">
              <span class="mono small">{{ row.data_budget }} / {{ row.member_engine }}</span>
            </template>
          </el-table-column>
          <el-table-column label="12 年平均 F1" width="130">
            <template #default="{ row }">
              <span class="mono strong">{{ fmtF1(row.mean_f1_12y) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="F1-2023" width="100">
            <template #default="{ row }"><span class="mono">{{ fmtF1(row.f1_2023) }}</span></template>
          </el-table-column>
          <el-table-column label="F1-2024" width="100">
            <template #default="{ row }"><span class="mono">{{ fmtF1(row.f1_2024) }}</span></template>
          </el-table-column>
          <el-table-column label="墙钟" width="105">
            <template #default="{ row }"><span class="mono">{{ fmtWall(row.wall_seconds) }}</span></template>
          </el-table-column>
          <el-table-column label="来源" min-width="220">
            <template #default="{ row }">
              <span class="muted small">runs/diagnostics/ch5-system/{{ row.cell }}-result.json</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="92" align="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openCell(row.cell)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="table-note">
          入口差异：上方任务表为本次平台 E2E 收据（Go 后端 exec → `ch5_system_runner.py`）；
          本表为 `ch5_system_runner.py` 直接运行的 CLI 收据。两者共用同一数据、冻结协议与评测代码，
          仅运行入口不同。<template v-if="missingRows.length">
            缺格：<span class="mono">{{ missingRows.join(', ') }}</span>。
          </template>
        </div>
      </div>
    </div>

    <div class="grid grid-3" style="margin-top: 14px">
      <div class="card">
        <div class="card-head">
          <div class="card-title">任务状态机与串行纪律<small>单工作协程</small></div>
        </div>
        <div class="card-body tight">
          <div class="state-flow">
            <div class="state-node">
              <span class="pill info">pending</span>
              <div>写入任务表</div>
            </div>
            <div class="state-arrow">→</div>
            <div class="state-node">
              <span class="pill warn">running</span>
              <div>子进程执行</div>
            </div>
            <div class="state-arrow">→</div>
            <div class="state-node">
              <span class="pill ok">completed</span>
              <div>快照落库</div>
            </div>
          </div>
          <div class="table-note">
            退出码非零、结果缺失或不可解析、cell 不符、结果文件早于本次开始时间，均记为 failed；
            同刻最多一个 MPS 训练子进程。
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-title">运行入口与产物<small>平台 / CLI</small></div>
        </div>
        <div class="card-body tight">
          <div class="assert-list">
            <div class="assert-row">
              <span class="k">平台任务</span>
              <span class="v">Go exec → ch5_system_runner.py</span>
            </div>
            <div class="assert-row">
              <span class="k">任务日志</span>
              <span class="v">runs/diagnostics/ch5-system/task_&lt;id&gt;.log</span>
            </div>
            <div class="assert-row">
              <span class="k">结果快照</span>
              <span class="v">metrics_json（完成时写入）</span>
            </div>
            <div class="assert-row">
              <span class="k">CLI 收据</span>
              <span class="v">{cell}-result.json</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-title">验收口径<small>功能与性能</small></div>
        </div>
        <div class="card-body tight">
          <div class="assert-list">
            <div class="assert-row">
              <span class="k">功能</span>
              <span class="v">双开关映射 · 生命周期 · 快照</span>
            </div>
            <div class="assert-row">
              <span class="k">性能</span>
              <span class="v">提交→完成墙钟 · 资源采样</span>
            </div>
            <div class="assert-row">
              <span class="k">证据</span>
              <span class="v">tasks 行 · 日志 · 结果 JSON</span>
            </div>
            <div class="assert-row">
              <span class="k">隔离</span>
              <span class="v">同 cell 后续运行不覆盖快照</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="source-line">
      <b>任务表来源：</b>GET /api/tasks（MySQL `tasks` 表，按 ID 降序）；
      <b>归档收据：</b>{{ manifest?.source_root || 'thesis/experiments/llm_probe/runs/diagnostics' }}；
      <b>对比文件时间：</b>{{ fmtDateTime(comparison?.ts) }}。
    </div>
  </div>
</template>
