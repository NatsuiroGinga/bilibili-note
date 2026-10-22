<script setup>
import { computed } from 'vue'
import { cellMeta, fmtDateTime, fmtF1, fmtInt, fmtWall } from '../format'

const props = defineProps({
  result: { type: Object, required: true },
  task: { type: Object, default: null },
  sourceLabel: { type: String, default: '' },
  sourcePath: { type: String, default: '' },
})

const config = computed(() => props.result?.config || {})
const model = computed(() => props.result?.model || {})
const contract = computed(() => model.value?.contract || {})
const consistency = computed(() => props.result?.eval_consistency || {})
const equivalence = computed(() => props.result?.equivalence || null)
const protocol = computed(() => props.result?.protocol || {})
const efficiency = computed(() => props.result?.efficiency || {})
const meta = computed(() => cellMeta(props.result?.cell || ''))

function boolText(value) {
  if (value === true) return '通过'
  if (value === false) return '未通过'
  return '-'
}

const platformWallSeconds = computed(() => {
  if (props.task?.created_at && props.task?.finished_at) {
    const delta = (new Date(props.task.finished_at) - new Date(props.task.created_at)) / 1000
    if (Number.isFinite(delta) && delta >= 0) return delta
  }
  return null
})
const kernelWallSeconds = computed(() => efficiency.value?.wall_seconds_cell ?? null)
</script>

<template>
  <div class="assertion-stack">
    <div class="card">
      <div class="card-head">
        <div class="card-title">配置断言摘要<small>开关映射与模型契约</small></div>
        <span class="pill" :class="consistency.passed === false ? 'warn' : 'ok'">
          {{ consistency.passed === false ? '断言未通过' : '断言通过' }}
        </span>
      </div>
      <div class="card-body tight">
        <div class="assert-list">
          <div class="assert-row">
            <span class="k">运行入口</span>
            <span class="v">{{ task ? `平台任务 #${task.id}（Go 后端 exec）` : 'CLI 归档制品' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">数据预算</span>
            <span class="v">{{ config.data_budget || '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">成员引擎</span>
            <span class="v">{{ config.member_engine || '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">四格</span>
            <span class="v">{{ meta.short }} · {{ meta.title }}</span>
          </div>
          <div class="assert-row">
            <span class="k">模型类</span>
            <span class="v">{{ model.class || '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">成员数 k</span>
            <span class="v">{{ model.member_k ?? '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">参数量</span>
            <span class="v">{{ fmtInt(model.n_params) }}</span>
          </div>
          <div class="assert-row">
            <span class="k">契约断言</span>
            <span class="v">
              参数量 {{ boolText(contract.params_match) }} · 成员数 {{ boolText(contract.member_k_matches) }}
            </span>
          </div>
          <div class="assert-row">
            <span class="k">评测一致性</span>
            <span class="v">
              {{ boolText(consistency.passed) }} · |ΔF1| = {{ fmtF1(consistency.abs_diff, 6) }}
            </span>
          </div>
          <div v-if="equivalence" class="assert-row">
            <span class="k">等价性断言</span>
            <span class="v">
              {{ boolText(equivalence.passed) }} · max |Δ| = {{ fmtF1(equivalence.max_abs_delta, 6) }}
            </span>
          </div>
          <div class="assert-row">
            <span class="k">平台提交→完成</span>
            <span class="v">{{ task ? fmtWall(platformWallSeconds) : '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">内核执行墙钟</span>
            <span class="v">{{ fmtWall(kernelWallSeconds) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div class="card-title">冻结协议与溯源<small>单一冻结种子</small></div>
      </div>
      <div class="card-body tight">
        <div class="assert-list">
          <div class="assert-row">
            <span class="k">随机种子 / 批量</span>
            <span class="v">{{ protocol.seed ?? '-' }} / {{ protocol.batch ?? '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">训练轮数</span>
            <span class="v">{{ protocol.epochs ?? '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">优化器</span>
            <span class="v">
              {{ protocol.optimizer_type || '-' }}({{ protocol.lr }}, {{ protocol.momentum }})
            </span>
          </div>
          <div class="assert-row">
            <span class="k">权重衰减 / 阈值</span>
            <span class="v">{{ protocol.weight_decay ?? '-' }} / {{ protocol.threshold ?? '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">回放记忆 / 设备</span>
            <span class="v">{{ protocol.memory ?? '-' }} / {{ protocol.device ?? '-' }}</span>
          </div>
          <div class="assert-row">
            <span class="k">回评口径</span>
            <span class="v">末年模型对 12 个年度测试分片打分</span>
          </div>
          <div class="assert-row">
            <span class="k">结果时间戳</span>
            <span class="v">{{ fmtDateTime(result.ts) }}</span>
          </div>
        </div>
        <div class="source-line">
          <b>读数来源：</b>{{ sourceLabel }}
          <template v-if="sourcePath"><br /><b>制品路径：</b>{{ sourcePath }}</template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.assertion-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.assert-row {
  padding: 3.2px 0;
  font-size: 11.2px;
}

.assert-row .v {
  font-size: 11px;
}

:deep(.card-head) {
  padding: 10px 16px 9px;
}

:deep(.card-body.tight) {
  padding: 8px 12px;
}

.source-line {
  margin-top: 8px;
  padding: 7px 10px;
  font-size: 10.8px;
}
</style>
