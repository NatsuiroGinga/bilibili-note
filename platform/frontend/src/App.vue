<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getHealth } from './api'

const route = useRoute()
const health = ref(null)
const healthError = ref('')

const navItems = [
  { key: 'config', label: '实验配置', to: '/' },
  { key: 'tasks', label: '任务列表', to: '/tasks' },
  { key: 'detail', label: '结果详情', to: '/results/naive_members' },
  { key: 'comparison', label: '系统消融', to: '/comparison' },
]

const activeKey = computed(() => {
  if (route.path === '/') return 'config'
  if (route.path === '/tasks') return 'tasks'
  if (route.path.startsWith('/tasks/') || route.path.startsWith('/results/')) return 'detail'
  if (route.path.startsWith('/comparison')) return 'comparison'
  return ''
})

const healthLabel = computed(() => {
  if (healthError.value) return '后端未连接'
  if (!health.value) return '正在连接后端'
  if (health.value.backend === 'mysql') return 'MySQL 已连接 · 串行队列'
  return '内存存储（开发模式）'
})

onMounted(async () => {
  try {
    health.value = await getHealth()
  } catch (error) {
    healthError.value = error.message
  }
})
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand">
        <div class="brand-mark">LAMDA</div>
        <div>
          <div class="brand-title">长期概念漂移检测训练平台</div>
          <div class="brand-sub">第五章 · Web 平台 · 双开关系统消融与年度面板评测</div>
        </div>
      </div>
      <nav class="app-nav">
        <router-link
          v-for="item in navItems"
          :key="item.key"
          :to="item.to"
          class="nav-link"
          :class="{ active: activeKey === item.key }"
        >
          {{ item.label }}
        </router-link>
      </nav>
      <div class="header-status">
        <span class="dot" :class="{ warn: healthError || health?.backend === 'memory' }"></span>
        <span>{{ healthLabel }}</span>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>
