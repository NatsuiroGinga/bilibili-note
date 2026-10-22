<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  createTask,
  getHealth,
  listTasks,
  loadComparisonSnapshot,
} from '../api'
import { cellFromSwitches, cellMeta, fmtDateTime, fmtF1, fmtWall, statusMeta } from '../format'
import { markPageReady, resetPageReady } from '../ready'

const router = useRouter()
const form = reactive({ data_budget: 'naive', member_engine: 'off' })
const submitting = ref(false)
const tasks = ref([])
const health = ref(null)
const comparison = ref(null)

const memberOn = computed({
  get: () => form.member_engine === 'tabm4',
  set: (value) => {
    form.member_engine = value ? 'tabm4' : 'off'
  },
})

const currentCell = computed(() => cellFromSwitches(form.data_budget, form.member_engine))
const currentMeta = computed(() => cellMeta(currentCell.value))
const lastTask = computed(() => tasks.value[0] || null)

const counts = computed(() => {
  const result = { pending: 0, running: 0, completed: 0, failed: 0 }
  for (const task of tasks.value) {
    if (result[task.status] !== undefined) result[task.status] += 1
  }
  return result
})

const readonlyParams = [
  { k: '随机种子', v: '42' },
  { k: '批量大小', v: '1024' },
  { k: '训练轮数', v: '10' },
  { k: '优化器', v: 'SGD' },
  { k: '学习率', v: '0.01' },
  { k: '动量', v: '0.9' },
  { k: '权重衰减', v: '1e-6' },
  { k: '判定阈值', v: '0.5' },
  { k: '回放记忆', v: '200' },
  { k: '计算设备', v: 'mps' },
  { k: '回评口径', v: '末年回评 12 年' },
  { k: '结果文件', v: '{cell}-result.json' },
]

const cellItems = computed(() =>
  ['naive', 'replay', 'naive_members', 'full'].map((cell) => ({
    ...cellMeta(cell),
    active: currentCell.value === cell,
  })),
)

function matrixState(cell) {
  const row = comparison.value?.cells?.[cell]
  const task = tasks.value.find((item) => item.cell === cell && ['pending', 'running'].includes(item.status))
  if (task) return { kind: task.status, label: statusMeta(task.status).label, mean: null }
  if (row) return { kind: 'done', label: 'CLI 已入库', mean: row.mean_f1_12y }
  if (comparison.value?.missing_cells?.includes(cell)) return { kind: 'missing', label: '训练中', mean: null }
  return { kind: 'idle', label: '未运行', mean: null }
}

const matrixRows = computed(() => {
  const rows = [
    { budget: 'naive', label: 'naive 预算', cells: ['naive', 'naive_members'] },
    { budget: 'quota_deficit', label: 'quota_deficit 预算', cells: ['replay', 'full'] },
  ]
  return rows.map((row) => ({
    ...row,
    items: row.cells.map((cell) => ({ ...cellMeta(cell), state: matrixState(cell) })),
  }))
})

const lastTaskState = computed(() => (lastTask.value ? statusMeta(lastTask.value.status) : null))

async function refreshQuietly() {
  const results = await Promise.allSettled([
    getHealth(),
    listTasks(),
    loadComparisonSnapshot(),
  ])
  if (results[0].status === 'fulfilled') health.value = results[0].value
  if (results[1].status === 'fulfilled') tasks.value = results[1].value
  if (results[2].status === 'fulfilled') comparison.value = results[2].value.data
}

async function submit() {
  submitting.value = true
  try {
    const task = await createTask({
      data_budget: form.data_budget,
      member_engine: form.member_engine,
    })
    ElMessage.success(`任务 #${task.id} 已提交，进入串行队列`)
    tasks.value = [task, ...tasks.value]
    router.push('/tasks')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  resetPageReady()
  await refreshQuietly()
  markPageReady(700)
})
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h1 class="page-title">实验配置与任务提交</h1>
        <div class="page-sub">
          双开关按 2×2 系统消融契约映射到四格；提交后由 Go 后端串行队列调用同一训练内核，
          平台不改变任何训练语义、数值或判据。
        </div>
      </div>
      <div class="page-head-right">
        <span class="pill info">配置冻结 · 2026-10-22</span>
        <span class="pill">单一冻结种子</span>
      </div>
    </div>

    <div
      v-if="lastTask"
      class="status-banner"
      :class="lastTask.status === 'completed' ? 'ok' : lastTask.status === 'failed' ? 'warn' : 'info'"
    >
      <span class="pill" :class="lastTask.status === 'completed' ? 'ok' : 'warn'">{{ lastTaskState?.label }}</span>
      <span>
        最近一次平台提交：任务 #{{ lastTask.id }} · {{ cellMeta(lastTask.cell).short }} ·
        提交于 {{ fmtDateTime(lastTask.created_at) }}
        <template v-if="lastTask.finished_at"> · 完成于 {{ fmtDateTime(lastTask.finished_at) }}</template>
      </span>
      <span class="spacer"></span>
      <router-link :to="`/tasks/${lastTask.id}`" style="color: inherit; font-weight: 600">查看任务结果</router-link>
    </div>

    <div v-else class="status-banner info">
      <span class="dot warn"></span>
      当前队列尚无平台任务；提交后将写入 MySQL 并由串行队列执行。
    </div>

    <div class="config-layout">
      <div class="card">
        <div class="card-head">
          <div class="card-title">双开关实验配置<small>data_budget × member_engine</small></div>
          <span class="pill info">POST /api/tasks · 串行执行</span>
        </div>
        <div class="card-body">
          <el-form label-position="top">
            <div class="grid grid-2" style="gap: 20px">
              <el-form-item label="数据预算（data_budget）">
                <el-select v-model="form.data_budget" size="large">
                  <el-option label="naive · 朴素预算（无历史回放）" value="naive" />
                  <el-option label="quota_deficit · 配额赤字感知回放" value="quota_deficit" />
                </el-select>
                <div class="switch-note">
                  控制经验回放构成器是否启用配额赤字感知；第三章回放构成器的开/关。
                </div>
              </el-form-item>
              <el-form-item label="成员引擎（member_engine）">
                <div class="row gap-12" style="min-height: 40px">
                  <el-switch
                    v-model="memberOn"
                    size="large"
                    active-text="tabm4"
                    inactive-text="off"
                    style="--el-switch-on-color: #1e5f96"
                  />
                  <span class="pill" :class="memberOn ? 'ok' : ''">
                    {{ memberOn ? 'TabM 4 成员已启用' : '单模型执行' }}
                  </span>
                </div>
                <div class="switch-note">
                  控制第四章成员化引擎；开启后由 4 个成员共享底座输出 sigmoid 概率均值。
                </div>
              </el-form-item>
            </div>

            <div class="form-section-label">
              映射到四格
              <span class="tag-cell" :class="currentCell">{{ currentMeta.short }}</span>
            </div>
            <div class="cell-map">
              <div
                v-for="item in cellItems"
                :key="item.key"
                class="cell-map-item"
                :class="{ active: item.active }"
              >
                <div class="row gap-8">
                  <span class="tag-cell" :class="item.key">{{ item.short }}</span>
                  <span class="strong small">{{ item.title }}</span>
                </div>
                <div class="switches">{{ item.budget }} / {{ item.engine }}</div>
              </div>
            </div>

            <div class="form-section-label" style="margin-top: 16px">冻结参数（只读）</div>
            <div class="readonly-grid">
              <div v-for="item in readonlyParams" :key="item.k" class="readonly-item">
                <div class="k">{{ item.k }}</div>
                <div class="v" :title="item.v">{{ item.v }}</div>
              </div>
            </div>

            <div class="row gap-12" style="margin-top: 18px">
              <el-button type="primary" size="large" :loading="submitting" @click="submit">
                提交训练任务
              </el-button>
              <span class="muted small">
                经 `/api/tasks` 写入任务表；同一时刻最多一个 MPS 训练子进程。
              </span>
            </div>
          </el-form>
        </div>
      </div>

      <div class="detail-side">
        <div class="card">
          <div class="card-head">
            <div class="card-title">平台运行状态<small>Go/Gin · GORM/MySQL</small></div>
            <span class="pill ok">{{ health?.backend === 'mysql' ? 'MySQL 已连接' : '连接检查中' }}</span>
          </div>
          <div class="card-body tight">
            <div class="assert-list">
              <div class="assert-row">
                <span class="k">存储后端</span>
                <span class="v">{{ health?.backend || '-' }}</span>
              </div>
              <div class="assert-row">
                <span class="k">任务队列</span>
                <span class="v">
                  排队 {{ counts.pending }} · 运行 {{ counts.running }} · 完成 {{ counts.completed }} · 失败 {{ counts.failed }}
                </span>
              </div>
              <div class="assert-row">
                <span class="k">最近提交</span>
                <span class="v">{{ lastTask ? `#${lastTask.id} ${cellMeta(lastTask.cell).short}` : '无' }}</span>
              </div>
              <div class="assert-row">
                <span class="k">执行入口</span>
                <span class="v">Go exec → ch5_system_runner.py</span>
              </div>
              <div class="assert-row">
                <span class="k">任务执行墙钟</span>
                <span class="v">{{ lastTask ? fmtWall(lastTask.started_at && lastTask.finished_at ? (new Date(lastTask.finished_at) - new Date(lastTask.started_at)) / 1000 : null) : '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="card" style="margin-top: 14px">
          <div class="card-head">
            <div class="card-title">四格矩阵<small>CLI 收据与平台队列</small></div>
          </div>
          <div class="card-body tight">
            <div class="matrix">
              <div class="matrix-head"></div>
              <div class="matrix-head">member_engine = off</div>
              <div class="matrix-head">member_engine = tabm4</div>
              <template v-for="row in matrixRows" :key="row.budget">
                <div class="matrix-row-label">{{ row.label }}</div>
                <div
                  v-for="item in row.items"
                  :key="item.key"
                  class="matrix-cell"
                  :class="item.state.kind === 'done' ? 'done' : item.state.kind === 'missing' ? 'missing' : ''"
                >
                  <div class="name">{{ item.short }}</div>
                  <div class="state">{{ item.state.label }}</div>
                  <div class="mean">{{ item.state.mean === null ? '—' : fmtF1(item.state.mean) }}</div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div class="card" style="margin-top: 14px">
          <div class="card-head">
            <div class="card-title">数据与评测口径<small>只读溯源</small></div>
          </div>
          <div class="card-body tight">
            <div class="small muted" style="line-height: 1.65">
              12 年面板：末年 experience（2025）的模型对 2013–2025 共 12 个年度测试分片逐样本打分；
              当年指标在每个 experience 训练结束后立即评价。
            </div>
            <div class="source-line">
              <b>四格收据：</b>runs/diagnostics/ch5-system/system-comparison.json
              <template v-if="comparison"><br /><b>收据时间：</b>{{ fmtDateTime(comparison.ts) }}</template>
              <br /><b>说明：</b>四格收据为构建期只读快照；平台任务读数为任务表实时快照。
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
