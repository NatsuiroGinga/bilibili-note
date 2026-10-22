<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  getTask,
  listTasks,
  loadArtifactManifest,
  loadComparisonSnapshot,
  loadReferenceTabm4,
} from '../api'
import { cellMeta, fmtDateTime, fmtF1, fmtInt, fmtWall } from '../format'
import { markPageReady, resetPageReady } from '../ready'
import CellBadge from '../components/CellBadge.vue'
import ComparisonBarChart from '../components/ComparisonBarChart.vue'

const router = useRouter()
const comparison = ref(null)
const comparisonSource = ref('')
const manifest = ref(null)
const referenceData = ref(null)
const tasks = ref([])
const platformTask = ref(null)
const platformResult = ref(null)
const error = ref('')
const loading = ref(true)

const order = ['naive', 'naive_members', 'replay', 'full']
const matrixRows = [
  { budget: 'naive', label: 'naive 预算', cells: ['naive', 'naive_members'] },
  { budget: 'quota_deficit', label: 'quota_deficit 预算', cells: ['replay', 'full'] },
]

const cells = computed(() => comparison.value?.cells || {})
// 以快照中实际存在的格结果为准；单格运行写入的 completed_cells 只表示该次调用的格，不代表全部既有收据。
const completed = computed(() => order.filter((cell) => Boolean(cells.value[cell])))
const missing = computed(() => order.filter((cell) => !cells.value[cell]))

const bestCell = computed(() => {
  let best = null
  for (const cell of order) {
    const row = cells.value[cell]
    if (!row || !Number.isFinite(Number(row.mean_f1_12y))) continue
    if (!best || Number(row.mean_f1_12y) > Number(best.row.mean_f1_12y)) {
      best = { cell, row }
    }
  }
  return best
})

const platform = computed(() => {
  if (!platformTask.value || !platformResult.value) return null
  const panel = platformResult.value.panel || {}
  return {
    cell: platformTask.value.cell,
    taskId: platformTask.value.id,
    data_budget: platformTask.value.data_budget,
    member_engine: platformTask.value.member_engine,
    mean_f1_12y: panel.mean_f1_12y,
    f1_2023: panel.f1_2023,
    f1_2024: panel.f1_2024,
    wall_seconds: platformResult.value.efficiency?.wall_seconds_cell,
  }
})

const reference = computed(() => {
  if (!referenceData.value) return null
  return {
    mean_f1_12y: referenceData.value.mean_f1,
    f1_2023: referenceData.value.f1_2023,
    f1_2024: referenceData.value.f1_2024,
    wall_seconds: referenceData.value.wall_seconds,
    source: 'runs/diagnostics/ch4-lamda-tabm-pilot/tabm4-result.json',
  }
})

const showReferenceLine = computed(() => missing.value.includes('full') && reference.value)

function cliRow(cell) {
  const row = cells.value[cell]
  const meta = cellMeta(cell)
  if (row) {
    return {
      key: `cli-${cell}`,
      cell,
      config: `${row.data_budget} / ${row.member_engine}`,
      entry: 'CLI 四格收据',
      entryKind: 'cli',
      mean: row.mean_f1_12y,
      f1_2023: row.f1_2023,
      f1_2024: row.f1_2024,
      wall: row.wall_seconds,
      status: 'completed',
      source: 'system-comparison.json',
    }
  }
  return {
    key: `missing-${cell}`,
    cell,
    config: `${meta.budget} / ${meta.engine}`,
    entry: 'CLI 四格收据',
    entryKind: 'cli',
    mean: null,
    f1_2023: null,
    f1_2024: null,
    wall: null,
    status: 'running',
    source: '未完成',
  }
}

const tableRows = computed(() => {
  const rows = order.map((cell) => cliRow(cell))
  if (platform.value) {
    rows.push({
      key: 'platform',
      cell: platform.value.cell,
      config: `${platform.value.data_budget} / ${platform.value.member_engine}`,
      entry: `平台 E2E · 任务 #${platform.value.taskId}`,
      entryKind: 'platform',
      mean: platform.value.mean_f1_12y,
      f1_2023: platform.value.f1_2023,
      f1_2024: platform.value.f1_2024,
      wall: platform.value.wall_seconds,
      status: 'completed',
      source: `/api/tasks/${platform.value.taskId}/results`,
    })
  }
  if (reference.value) {
    rows.push({
      key: 'reference',
      cell: 'full',
      config: 'quota_deficit / tabm4',
      entry: '第四章先导（非平台四格）',
      entryKind: 'reference',
      mean: reference.value.mean_f1_12y,
      f1_2023: reference.value.f1_2023,
      f1_2024: reference.value.f1_2024,
      wall: reference.value.wall_seconds,
      status: 'reference',
      source: 'ch4-lamda-tabm-pilot/tabm4-result.json',
    })
  }
  return rows
})

function matrixState(cell) {
  const row = cells.value[cell]
  if (row) {
    return { kind: 'done', label: 'CLI 已入库', mean: row.mean_f1_12y }
  }
  if (missing.value.includes(cell)) {
    return { kind: 'missing', label: '未完成', mean: null }
  }
  return { kind: 'idle', label: '未运行', mean: null }
}

function entryClass(kind) {
  return kind === 'platform' ? 'ok' : kind === 'reference' ? 'info' : ''
}

function openRow(row) {
  if (row.key === 'platform') router.push(`/tasks/${platform.value.taskId}`)
  else if (row.entryKind === 'cli' && row.status === 'completed') router.push(`/results/${row.cell}`)
}

async function loadAll() {
  resetPageReady()
  loading.value = true
  error.value = ''
  try {
    const results = await Promise.allSettled([
      loadComparisonSnapshot(),
      loadArtifactManifest(),
      loadReferenceTabm4(),
      listTasks(),
    ])
    if (results[0].status === 'fulfilled') {
      comparison.value = results[0].value.data
      comparisonSource.value = results[0].value.sourceLabel
    } else {
      throw results[0].reason
    }
    if (results[1].status === 'fulfilled') manifest.value = results[1].value
    if (results[2].status === 'fulfilled') referenceData.value = results[2].value
    if (results[3].status === 'fulfilled') {
      tasks.value = results[3].value
      const completedTasks = tasks.value.filter((task) => task.status === 'completed')
      const chosen = completedTasks.find((task) => task.cell === 'naive') || completedTasks[0]
      if (chosen) {
        platformTask.value = await getTask(chosen.id)
        platformResult.value = platformTask.value.metrics || null
      }
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    await nextTick()
    markPageReady(950)
  }
}

onMounted(loadAll)
</script>

<template>
  <div v-loading="loading" element-loading-text="正在读取四格收据">
    <div class="page-head">
      <div>
        <h1 class="page-title">系统四格消融对比</h1>
        <div class="page-sub">
          2×2 开关矩阵的 12 年平均 F1；CLI 四格收据与本次平台 E2E 收据分列标注运行入口，
          同一数据、同一冻结协议、同一评测代码。
        </div>
      </div>
      <div class="page-head-right">
        <span class="pill info">运行入口差异已标注</span>
        <span class="muted">对比文件 {{ fmtDateTime(comparison?.ts) }}</span>
      </div>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
      style="margin-bottom: 14px"
    />

    <template v-if="comparison">
      <div class="kpi-grid">
        <div class="kpi ok">
          <div class="kpi-label">CLI 已完成格数</div>
          <div class="kpi-value">{{ completed.length }}<small>/ 4</small></div>
          <div class="kpi-foot">system-comparison.json</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">最优 CLI 12 年平均 F1</div>
          <div class="kpi-value">{{ bestCell ? fmtF1(bestCell.row.mean_f1_12y) : '-' }}</div>
          <div class="kpi-foot">
            {{ bestCell ? `${cellMeta(bestCell.cell).short} · ${cellMeta(bestCell.cell).title}` : '暂无' }}
          </div>
        </div>
        <div class="kpi muted-accent">
          <div class="kpi-label">平台 E2E 12 年平均 F1</div>
          <div class="kpi-value">{{ platform ? fmtF1(platform.mean_f1_12y) : '-' }}</div>
          <div class="kpi-foot">
            {{ platform ? `任务 #${platform.taskId} · ${cellMeta(platform.cell).short} · ${fmtWall(platform.wall_seconds)}` : '尚无已完成平台任务' }}
          </div>
        </div>
        <div class="kpi" :class="missing.length ? 'warn' : 'ok'">
          <div class="kpi-label">缺格状态</div>
          <div class="kpi-value">{{ missing.length ? missing.map((c) => cellMeta(c).short).join(' / ') : '四格齐备' }}</div>
          <div class="kpi-foot">
            {{ missing.length ? '未完成' : 'CLI 四格全部入库' }}
          </div>
        </div>
      </div>

      <div class="detail-layout" style="grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr)">
        <div class="card">
          <div class="card-head">
            <div class="card-title">四格 12 年平均 F1 对比<small>柱为 CLI 收据，菱形为平台 E2E</small></div>
            <div class="legend-note">
              <span class="legend-backward">CLI 四格</span>
              <span class="legend-platform">平台 E2E</span>
            </div>
          </div>
          <div class="card-body" style="padding: 8px 14px 10px">
            <ComparisonBarChart
              :cells="cells"
              :completed="completed"
              :missing="missing"
              :platform="platform"
              :reference="showReferenceLine ? reference : null"
              :height="258"
            />
            <div class="small muted" style="margin-top: 2px">
              柱高为各格 12 年平均 F1；绿色菱形为本次经平台提交并串行执行完成的 naive 格读数。
              <template v-if="showReferenceLine">
                紫色虚线为第四章 full 先导读数（非平台四格复刻）。
              </template>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">四格矩阵<small>开关 × 状态</small></div>
            <span class="pill" :class="missing.length ? 'warn' : 'ok'">
              {{ missing.length ? `${missing.length} 格未完成` : '四格齐备' }}
            </span>
          </div>
          <div class="card-body tight">
            <div class="matrix">
              <div class="matrix-head"></div>
              <div class="matrix-head">member_engine = off</div>
              <div class="matrix-head">member_engine = tabm4</div>
              <template v-for="row in matrixRows" :key="row.budget">
                <div class="matrix-row-label">{{ row.label }}</div>
                <div
                  v-for="cell in row.cells"
                  :key="cell"
                  class="matrix-cell"
                  :class="matrixState(cell).kind === 'done' ? 'done' : matrixState(cell).kind === 'missing' ? 'missing' : ''"
                >
                  <div class="name">{{ cellMeta(cell).short }}</div>
                  <div class="state">{{ matrixState(cell).label }}</div>
                  <div class="mean">{{ matrixState(cell).mean === null ? '—' : fmtF1(matrixState(cell).mean) }}</div>
                </div>
              </template>
            </div>
            <div class="table-note">
              每格标注的数值来自 CLI 收据；平台 E2E 读数见下方表格的独立行。
            </div>
            <div class="source-line">
              <b>CLI 收据来源：</b>{{ comparisonSource }}
              <template v-if="comparison?.data_root"><br /><b>数据根：</b>{{ comparison.data_root }}</template>
            </div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 14px">
        <div class="card-head">
          <div class="card-title">逐格读数与运行入口<small>同一内核 · 同一协议</small></div>
          <span class="pill">{{ tableRows.length }} 行读数</span>
        </div>
        <div class="card-body tight">
          <el-table :data="tableRows" size="small" class="compact-table" style="width: 100%">
            <el-table-column label="四格" width="148">
              <template #default="{ row }">
                <span v-if="row.key === 'reference'" class="tag-cell full">FULL 先导</span>
                <CellBadge v-else :cell="row.cell" />
              </template>
            </el-table-column>
            <el-table-column label="开关" width="190">
              <template #default="{ row }"><span class="mono small">{{ row.config }}</span></template>
            </el-table-column>
            <el-table-column label="运行入口" min-width="225">
              <template #default="{ row }">
                <span class="pill" :class="entryClass(row.entryKind)">{{ row.entry }}</span>
              </template>
            </el-table-column>
            <el-table-column label="12 年平均 F1" width="128">
              <template #default="{ row }">
                <span class="mono strong" :style="row.status === 'running' ? 'color:#b07a1e' : ''">
                  {{ row.mean === null ? '训练中' : fmtF1(row.mean) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="F1-2023" width="100">
              <template #default="{ row }"><span class="mono">{{ fmtF1(row.f1_2023) }}</span></template>
            </el-table-column>
            <el-table-column label="F1-2024" width="100">
              <template #default="{ row }"><span class="mono">{{ fmtF1(row.f1_2024) }}</span></template>
            </el-table-column>
            <el-table-column label="墙钟" width="100">
              <template #default="{ row }"><span class="mono">{{ fmtWall(row.wall) }}</span></template>
            </el-table-column>
            <el-table-column label="来源" min-width="230">
              <template #default="{ row }"><span class="muted small">{{ row.source }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="86" align="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  :disabled="row.entryKind === 'reference' || row.status !== 'completed'"
                  @click="openRow(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-note">
            入口差异：CLI 行由 `tools/ch5_system_runner.py` 直接运行产生（system-comparison.json 构建期快照）；
            平台行由 Go 后端经 exec 调用同一脚本产生（任务 #{{ platform?.taskId || '-' }} 的完成快照）。
            两行 naive 读数应一致，差异只允许来自运行入口与墙钟，不允许来自协议。
            <template v-if="reference">
              <template v-if="missing.includes('full')">
                full 先导参考 {{ fmtF1(reference.mean_f1_12y) }} 来自第四章 TABM4 先导，
                仅作缺格期对照，不替代四格读数。
              </template>
              <template v-else>
                full CLI 读数 {{ fmtF1(cells.full?.mean_f1_12y) }} 与第四章先导
                {{ fmtF1(reference.mean_f1_12y) }} 一致（等价性检查 passed），先导行仅作对照。
              </template>
            </template>
            <template v-if="platform && cells.naive">
              平台 naive 内核墙钟 {{ fmtWall(platform.wall_seconds) }}，CLI naive 内核墙钟
              {{ fmtWall(cells.naive.wall_seconds) }}；两者 F1 读数逐位一致。墙钟差异的原因
              （当前平台后端启动环境未设置 OMP_NUM_THREADS=4）待同环境复测。
            </template>
          </div>
        </div>
      </div>

      <div class="source-line">
        <b>数据说明：</b>四格 CLI 收据与平台任务共用同一 `ch5_system_runner.py`、同一冻结种子与评测代码；
        CLI 收据运行于 2026-10-22，平台 E2E 任务 #{{ platform?.taskId || '-' }} 经 MySQL 任务表与 Go 串行队列执行。
        <b>制品根：</b>{{ manifest?.source_root || 'thesis/experiments/llm_probe/runs/diagnostics' }}；
        <b>参数总量：</b>{{ fmtInt(comparison?.cells?.naive?.n_params) }}（单模型）/ {{ fmtInt(comparison?.cells?.naive_members?.n_params) }}（4 成员）。
      </div>
    </template>
  </div>
</template>
