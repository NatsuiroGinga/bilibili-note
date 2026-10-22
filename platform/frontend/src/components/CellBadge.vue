<script setup>
import { computed } from 'vue'
import { cellMeta } from '../format'

const props = defineProps({
  cell: { type: String, default: '' },
})

const meta = computed(() => cellMeta(props.cell))
</script>

<template>
  <el-tooltip :content="`${meta.title}（${meta.budget} / ${meta.engine}）`" placement="top">
    <span class="tag-cell" :class="cell">{{ meta.short }}</span>
  </el-tooltip>
</template>
