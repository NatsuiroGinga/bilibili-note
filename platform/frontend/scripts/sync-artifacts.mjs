#!/usr/bin/env node
// 把仓库内已入库的第五章评测制品复制为前端只读静态资源。
// CLI 四格收据读 snapshots/ch5-cli/ 的冻结副本：平台 E2E 会覆盖 runs/ 中同名结果文件，
// 冻结副本保证图 5-7/5-8/5-10 的 CLI 行可复现；PROVENANCE.json 记录原始路径与哈希。
// 只复制、不改写任何数值；manifest 记录源路径、SHA256、字节数与修改时间。
import { copyFile, mkdir, readFile, rm, stat, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(here, '..')
const repoRoot = path.resolve(frontendRoot, '..', '..')
const diagnosticsRoot = path.join(
  repoRoot,
  'thesis',
  'experiments',
  'llm_probe',
  'runs',
  'diagnostics',
)
const snapshotRoot = path.join(frontendRoot, 'snapshots', 'ch5-cli')
const publicRoot = path.join(frontendRoot, 'public', 'artifacts')

const copies = [
  {
    key: 'system_comparison',
    source: path.join(snapshotRoot, 'system-comparison.json'),
    target: 'comparison/system-comparison.json',
    required: true,
  },
  {
    key: 'cell_naive',
    source: path.join(snapshotRoot, 'naive-result.json'),
    target: 'cells/naive-result.json',
    required: false,
    cell: 'naive',
  },
  {
    key: 'cell_replay',
    source: path.join(snapshotRoot, 'replay-result.json'),
    target: 'cells/replay-result.json',
    required: false,
    cell: 'replay',
  },
  {
    key: 'cell_naive_members',
    source: path.join(snapshotRoot, 'naive_members-result.json'),
    target: 'cells/naive_members-result.json',
    required: false,
    cell: 'naive_members',
  },
  {
    key: 'cell_full',
    source: path.join(snapshotRoot, 'full-result.json'),
    target: 'cells/full-result.json',
    required: false,
    cell: 'full',
  },
  {
    key: 'reference_tabm4',
    source: path.join(diagnosticsRoot, 'ch4-lamda-tabm-pilot', 'tabm4-result.json'),
    target: 'reference/tabm4-result.json',
    required: false,
  },
]

async function maybeStat(file) {
  try {
    return await stat(file)
  } catch (error) {
    if (error.code === 'ENOENT') return null
    throw error
  }
}

async function sha256(file) {
  const raw = await readFile(file)
  return createHash('sha256').update(raw).digest('hex')
}

const provenance = JSON.parse(await readFile(path.join(snapshotRoot, 'PROVENANCE.json'), 'utf8'))
const provenanceByFile = new Map(
  (provenance.files || []).map((item) => [path.basename(item.path), item]),
)

await rm(publicRoot, { recursive: true, force: true })
await mkdir(publicRoot, { recursive: true })

const files = []
const cells = []

for (const item of copies) {
  const info = await maybeStat(item.source)
  if (!info || !info.isFile()) {
    if (item.required) {
      throw new Error(`必需制品缺失：${item.source}`)
    }
    continue
  }
  const targetPath = path.join(publicRoot, item.target)
  await mkdir(path.dirname(targetPath), { recursive: true })
  await copyFile(item.source, targetPath)
  const record = {
    key: item.key,
    source: path.relative(repoRoot, item.source).split(path.sep).join('/'),
    target: `artifacts/${item.target}`,
    bytes: info.size,
    mtime: info.mtime.toISOString(),
    sha256: await sha256(item.source),
  }
  const original = provenanceByFile.get(path.basename(item.source))
  if (original) {
    record.original_source = original.original_source
    record.original_mtime = original.original_mtime
  }
  if (item.cell) {
    record.cell = item.cell
    cells.push(item.cell)
  }
  files.push(record)
}

const manifest = {
  schema_version: 'ch5-frontend-artifacts-v1',
  generated_at: new Date().toISOString(),
  source_root: 'thesis/experiments/llm_probe/runs/diagnostics',
  cli_snapshot_root: 'platform/frontend/snapshots/ch5-cli',
  cli_snapshot_provenance: 'platform/frontend/snapshots/ch5-cli/PROVENANCE.json',
  cli_snapshot_note:
    'CLI 四格收据为冻结副本；平台 E2E 会覆盖 runs/diagnostics/ch5-system/naive-result.json 与 system-comparison.json。',
  files,
  cells,
}

await writeFile(path.join(publicRoot, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
console.log(`已同步 ${files.length} 份制品到 ${path.relative(repoRoot, publicRoot)}；可用格：${cells.join(', ') || '无'}`)
