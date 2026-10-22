export const CELL_META = {
  naive: {
    key: 'naive',
    short: 'NAIVE',
    title: '朴素预算 · 单模型',
    budget: 'naive',
    engine: 'off',
  },
  replay: {
    key: 'replay',
    short: 'REPLAY',
    title: '配额赤字回放 · 单模型',
    budget: 'quota_deficit',
    engine: 'off',
  },
  naive_members: {
    key: 'naive_members',
    short: 'NAIVE+MEMBERS',
    title: '朴素预算 · 成员引擎',
    budget: 'naive',
    engine: 'tabm4',
  },
  full: {
    key: 'full',
    short: 'FULL',
    title: '配额赤字回放 · 成员引擎',
    budget: 'quota_deficit',
    engine: 'tabm4',
  },
}

export const STATUS_META = {
  pending: { label: '排队中', type: 'info' },
  running: { label: '运行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

export function cellMeta(cell) {
  return CELL_META[cell] || { key: cell, short: cell || '-', title: cell || '-', budget: '-', engine: '-' }
}

export function statusMeta(status) {
  return STATUS_META[status] || { label: status || '-', type: 'info' }
}

export function cellFromSwitches(budget, engine) {
  if (budget === 'naive' && engine === 'off') return 'naive'
  if (budget === 'quota_deficit' && engine === 'off') return 'replay'
  if (budget === 'naive' && engine === 'tabm4') return 'naive_members'
  if (budget === 'quota_deficit' && engine === 'tabm4') return 'full'
  return '-'
}

export function fmtF1(value, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(digits)
}

export function fmtPct(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return `${(Number(value) * 100).toFixed(digits)}%`
}

export function fmtWall(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  const total = Number(value)
  if (total < 60) return `${total.toFixed(1)} 秒`
  const minutes = Math.floor(total / 60)
  const seconds = total - minutes * 60
  return `${minutes} 分 ${seconds.toFixed(0)} 秒`
}

export function fmtInt(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toLocaleString('zh-CN')
}

export function fmtDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function fmtClock(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function durationBetween(start, finish) {
  if (!start || !finish) return null
  const delta = (new Date(finish).getTime() - new Date(start).getTime()) / 1000
  if (!Number.isFinite(delta) || delta < 0) return null
  return delta
}

export function taskWallSeconds(task) {
  if (task?.wall_seconds !== undefined && task?.wall_seconds !== null) {
    return Number(task.wall_seconds)
  }
  return durationBetween(task?.started_at, task?.finished_at)
}

export function yearsOf(panel) {
  const source = panel?.backward_f1 || panel?.current_year_f1 || {}
  return Object.keys(source).map(Number).sort((a, b) => a - b)
}
