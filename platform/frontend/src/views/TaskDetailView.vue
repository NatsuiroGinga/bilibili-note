<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getTask,
  getTaskResults,
  listTasks,
  loadCellResult,
  loadComparisonSnapshot,
} from '../api'
import {
  cellMeta,
  fmtDateTime,
  fmtF1,
  fmtInt,
  fmtWall,
  statusMeta,
  yearsOf,
} from '../format'
import { markPageReady, resetPageReady } from '../ready'
import CellBadge from '../components/CellBadge.vue'
import StatusTag from '../components/StatusTag.vue'
import F1LineChart from '../components/F1LineChart.vue'
import YearlyTable from '../components/YearlyTable.vue'
import ConfigAssertions from '../components/ConfigAssertions.vue'

const props = defineProps({
  id: { type: String, default: '' },
  cell: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const task = ref(null)
const result = ref(null)
const sourceLabel = ref('')
const sourcePath = ref('')
const tasks = ref([])
const comparison = ref(null)

const isCellMode = computed(() => route.name === 'cell-result')
const selectedValue = computed(() => (isCellMode.value ? `cell:${props.cell}` : `task:${props.id}`))
const activeCell = computed(() => result.value?.cell || task.value?.cell || props.cell)
const activeMeta = computed(() => cellMeta(activeCell.value))

const taskOptions = computed(() =>
  tasks.value.map((item) => ({
    value: `task:${item.id}`,
    label: `平台任务 #${item.id} · ${cellMeta(item.cell).short} · ${statusMeta(item.status).label}`,
  })),
)

const archiveOptions = computed(() => {
  const cells = comparison.value?.cells || {}
  return ['naive', 'naive_members', 'replay', 'full']
    .filter((cell) => cells[cell])
    .map((cell) => ({
      value: `cell:${cell}`,
      label: `归档 · ${cellMeta(cell).short} · 12y ${fmtF1(cells[cell].mean_f1_12y)}`,
    }))
})

const years = computed(() => yearsOf(result.value?.panel))
const meanF1 = computed(() => result.value?.panel?.mean_f1_12y)
const platformWallSeconds = computed(() => {
  if (task.value?.created_at && task.value?.finished_at) {
    const delta = (new Date(task.value.finished_at) - new Date(task.value.created_at)) / 1000
    if (Number.isFinite(delta) && delta >= 0) return delta
  }
  return null
})
const kernelWallSeconds = computed(() => result.value?.efficiency?.wall_seconds_cell ?? null)
const wallSeconds = computed(() =>
  platformWallSeconds.value !== null ? platformWallSeconds.value : kernelWallSeconds.value,
)
const consistencyPassed = computed(() => result.value?.eval_consistency?.passed === true)
const pendingStatus = computed(() =>
  task.value && ['pending', 'running'].includes(task.value.status) ? task.value.status : null,
)

async function loadTaskData() {
  const current = await getTask(props.id)
  task.value = current
  if (current.status === 'completed') {
    result.value = await getTaskResults(props.id)
    sourceLabel.value = `GET /api/tasks/${props.id}/results（任务完成时的结果快照）`
    sourcePath.value = `thesis/experiments/llm_probe/runs/diagnostics/ch5-system/${current.cell}-result.json`
  } else if (current.status === 'failed') {
    throw new Error(`任务 #${props.id} 失败，无可用结果；请到任务列表查看日志。`)
  }
}

async function loadCellData() {
  result.value = await loadCellResult(props.cell)
  sourceLabel.value = `artifacts/cells/${props.cell}-result.json（构建期从 runs/diagnostics 同步）`
  sourcePath.value = `thesis/experiments/llm_probe/runs/diagnostics/ch5-system/${props.cell}-result.json`
}

async function loadAll() {
  resetPageReady()
  loading.value = true
  error.value = ''
  task.value = null
  result.value = null
  try {
    const [tasksResult, comparisonResult] = await Promise.allSettled([
      listTasks(),
      loadComparisonSnapshot(),
    ])
    if (tasksResult.status === 'fulfilled') tasks.value = tasksResult.value
    if (comparisonResult.status === 'fulfilled') comparison.value = comparisonResult.value.data
    if (isCellMode.value) {
      await loadCellData()
    } else {
      await loadTaskData()
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    await nextTick()
    markPageReady(950)
  }
}

function onSelect(value) {
  if (!value) return
  const [kind, key] = value.split(':')
  if (kind === 'task') router.push(`/tasks/${key}`)
  else router.push(`/results/${key}`)
}

onMounted(loadAll)
watch(() => [props.id, props.cell, route.name], loadAll)
</script>

<template>
  <div v-loading="loading" element-loading-text="正在读取评测结果">
    <div class="page-head">
      <div>
        <h1 class="page-title">评测结果详情</h1>
        <div class="page-sub">
          12 年面板折线、逐年指标与配置断言；面板定义为末年 experience（2025）的模型对
          2013–2025 共 12 个年度测试分片逐样本打分。
        </div>
      </div>
      <div class="page-head-right">
        <CellBadge v-if="activeCell" :cell="activeCell" />
        <span class="pill" :class="consistencyPassed ? 'ok' : 'warn'">
          {{ consistencyPassed ? '评测一致性断言通过' : '断言读取中' }}
        </span>
      </div>
    </div>

    <div class="card selector-row">
      <span class="selector-label">选择任务 / 归档制品</span>
      <el-select
        :model-value="selectedValue"
        size="large"
        placeholder="选择平台任务或归档制品"
        @change="onSelect"
      >
        <el-option-group v-if="taskOptions.length" label="平台任务（MySQL）">
          <el-option v-for="item in taskOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-option-group>
        <el-option-group v-if="archiveOptions.length" label="归档制品（CLI 收据）">
          <el-option v-for="item in archiveOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-option-group>
      </el-select>
      <span class="spacer"></span>
      <StatusTag v-if="task" :status="task.status" />
      <span v-if="task" class="muted small">任务 #{{ task.id }} · 提交 {{ fmtDateTime(task.created_at) }}</span>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
      style="margin-bottom: 14px"
    />

    <div v-if="pendingStatus && !result" class="card" style="margin-bottom: 14px">
      <div class="card-body">
        <div class="status-banner" :class="pendingStatus === 'running' ? 'info' : 'warn'" style="margin-bottom: 0">
          <StatusTag :status="pendingStatus" />
          <span>
            任务 #{{ task.id }} 尚未完成，结果文件尚未生成。开始于 {{ fmtDateTime(task.started_at) }}；
            平台将串行完成训练、评价与打分后写入结果快照。
          </span>
        </div>
      </div>
    </div>

    <template v-if="result">
      <div class="kpi-grid">
        <div class="kpi ok">
          <div class="kpi-label">12 年平均 F1</div>
          <div class="kpi-value">{{ fmtF1(meanF1) }}</div>
          <div class="kpi-foot">末年模型统一回评 12 年</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">F1-2023</div>
          <div class="kpi-value">{{ fmtF1(result.f1_2023 ?? result.panel?.f1_2023) }}</div>
          <div class="kpi-foot">稀缺年 · n = {{ fmtInt(result.panel?.test_sizes?.['2023']?.n) }}</div>
        </div>
        <div class="kpi warn">
          <div class="kpi-label">F1-2024</div>
          <div class="kpi-value">{{ fmtF1(result.f1_2024 ?? result.panel?.f1_2024) }}</div>
          <div class="kpi-foot">稀缺年 · 正样本 {{ fmtInt(result.panel?.test_sizes?.['2024']?.n_pos) }}</div>
        </div>
        <div class="kpi muted-accent">
          <div class="kpi-label">本格墙钟</div>
          <div class="kpi-value">{{ fmtWall(wallSeconds) }}</div>
          <div class="kpi-foot">
            <template v-if="task">
              平台提交 → 完成 · 内核 {{ fmtWall(kernelWallSeconds) }}
            </template>
            <template v-else>CLI 直接运行</template>
            · {{ fmtInt(result.model?.n_params) }} 参数
          </div>
        </div>
      </div>

      <div class="detail-layout">
        <div>
          <div class="card">
            <div class="card-head">
              <div class="card-title">12 年面板 F1 折线<small>末年统一回评 vs 当年即时评价</small></div>
              <span class="pill info">{{ activeMeta.short }}</span>
            </div>
            <div class="card-body" style="padding: 8px 14px 10px">
              <F1LineChart
                :years="years"
                :backward="result.panel?.backward_f1 || {}"
                :current="result.panel?.current_year_f1 || {}"
                :height="208"
              />
              <div class="small muted" style="margin-top: 2px">
                阴影区为 2023–2025 稀缺年；2025 年测试分片仅 5 个正样本，两条曲线在该点均为 0。
              </div>
            </div>
          </div>

          <div class="card" style="margin-top: 14px">
            <div class="card-head">
              <div class="card-title">逐年指标<small>年度面板与稀缺年分面</small></div>
              <span class="pill">{{ activeMeta.short }} · {{ activeMeta.title }}</span>
            </div>
            <div class="card-body" style="padding: 8px 12px 10px">
              <YearlyTable :result="result" />
            </div>
          </div>
        </div>

        <div class="detail-side">
          <ConfigAssertions
            :result="result"
            :task="task"
            :source-label="sourceLabel"
            :source-path="sourcePath"
          />
        </div>
      </div>
    </template>
  </div>
</template>
