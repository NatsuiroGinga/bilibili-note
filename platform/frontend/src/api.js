// 平台 API 与只读制品读取。制品由 scripts/sync-artifacts.mjs 从 runs/diagnostics 复制，
// manifest 记录源路径与 SHA256；界面只展示，不改写任何数值。

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    cache: 'no-store',
    headers: { Accept: 'application/json', ...(options.headers || {}) },
    ...options,
  })
  const text = await response.text()
  let payload = null
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    payload = null
  }
  if (!response.ok) {
    const message = payload?.error || text || `HTTP ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.payload = payload
    throw error
  }
  return payload
}

export function getHealth() {
  return fetchJSON('/api/health')
}

export function listTasks() {
  return fetchJSON('/api/tasks')
}

export function getTask(id) {
  return fetchJSON(`/api/tasks/${encodeURIComponent(id)}`)
}

export function getTaskResults(id) {
  return fetchJSON(`/api/tasks/${encodeURIComponent(id)}/results`)
}

export function createTask(payload) {
  return fetchJSON('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// CLI 四格收据固定读构建期同步的只读快照。
// 原因：单格运行会重写源文件 system-comparison.json；平台 E2E 的 naive 运行也会覆盖同名结果文件，
// 快照保证界面展示的“CLI 收据”不被后续运行入口改写。平台读数另行从任务快照 API 读取。
export async function loadComparisonSnapshot() {
  const data = await fetchJSON('/artifacts/comparison/system-comparison.json')
  return {
    data,
    source: 'static',
    sourceLabel: 'artifacts/comparison/system-comparison.json（构建期 CLI 收据快照）',
  }
}

// 实时读取后端 /api/comparison；保留给需要观察当前源文件的场景，不用于 CLI 收据展示。
export async function loadComparisonLive() {
  return { data: await fetchJSON('/api/comparison'), source: 'api', sourceLabel: 'GET /api/comparison（实时）' }
}

export function loadArtifactManifest() {
  return fetchJSON('/artifacts/manifest.json')
}

export function loadCellResult(cell) {
  return fetchJSON(`/artifacts/cells/${encodeURIComponent(cell)}-result.json`)
}

export function loadReferenceTabm4() {
  return fetchJSON('/artifacts/reference/tabm4-result.json')
}

