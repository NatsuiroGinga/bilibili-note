#!/usr/bin/env node
// 逐页截图：1920×1080 PNG，落 thesis/figures/第五章/。
// 前置：Go 后端已在 CH5_BASE_URL 提供 dist 静态托管，且页面数据已就绪。
import { mkdir, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const here = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(here, '..')
const repoRoot = path.resolve(frontendRoot, '..', '..')
const figureDir = path.join(repoRoot, 'thesis', 'figures', '第五章')
const baseUrl = process.env.CH5_BASE_URL || 'http://127.0.0.1:8080'
const taskId = process.env.CH5_SHOT_TASK_ID || '1'

const shots = [
  {
    name: '图5-7-实验配置与双开关交互界面.png',
    path: '/',
  },
  {
    name: '图5-8-任务列表与状态页.png',
    path: '/tasks',
  },
  {
    name: '图5-9-评测结果12年面板可视化页.png',
    path: `/tasks/${taskId}`,
  },
  {
    name: '图5-10-系统四格消融对比页.png',
    path: '/comparison',
  },
]

await mkdir(figureDir, { recursive: true })

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  locale: 'zh-CN',
  timezoneId: 'Asia/Shanghai',
})
const page = await context.newPage()
page.on('console', (message) => {
  if (message.type() === 'error') console.log(`[page-error] ${message.text()}`)
})
page.on('pageerror', (error) => console.log(`[page-exception] ${error.message}`))

for (const shot of shots) {
  const url = `${baseUrl}${shot.path}`
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
  await page.waitForFunction(() => window.__PAGE_READY__ === true, { timeout: 45000 })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(900)
  const target = path.join(figureDir, shot.name)
  await page.screenshot({ path: target, fullPage: false })
  const info = await stat(target)
  console.log(`${shot.name}\t${info.size} bytes\t${url}`)
}

await browser.close()
console.log(`截图目录：${figureDir}`)
