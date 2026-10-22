<script setup>
import { computed } from 'vue'
import { statusMeta } from '../format'

const props = defineProps({
  status: { type: String, default: '' },
})

const meta = computed(() => statusMeta(props.status))
</script>

<template>
  <el-tag :type="meta.type" size="small" effect="light" round>
    {{ meta.label }}
  </el-tag>
</template>
