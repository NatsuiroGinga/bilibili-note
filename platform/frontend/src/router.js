import { createRouter, createWebHistory } from 'vue-router'
import ConfigView from './views/ConfigView.vue'
import TaskListView from './views/TaskListView.vue'
import TaskDetailView from './views/TaskDetailView.vue'
import ComparisonView from './views/ComparisonView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'config', component: ConfigView, meta: { title: '实验配置' } },
    { path: '/tasks', name: 'tasks', component: TaskListView, meta: { title: '任务列表' } },
    {
      path: '/tasks/:id',
      name: 'task-detail',
      component: TaskDetailView,
      props: true,
      meta: { title: '结果详情' },
    },
    {
      path: '/results/:cell',
      name: 'cell-result',
      component: TaskDetailView,
      props: true,
      meta: { title: '结果详情' },
    },
    {
      path: '/comparison',
      name: 'comparison',
      component: ComparisonView,
      meta: { title: '系统消融' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
