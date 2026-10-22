<script setup>
import { computed } from 'vue'
import { fmtF1, fmtInt, yearsOf } from '../format'

const props = defineProps({
  result: { type: Object, required: true },
})

const rows = computed(() => {
  const panel = props.result?.panel || {}
  const perYear = props.result?.per_year || {}
  return yearsOf(panel).map((year) => {
    const metrics = panel.current_year_metrics?.[String(year)] || {}
    const backward = panel.backward_f1?.[String(year)]
    const current = panel.current_year_f1?.[String(year)]
    return {
      year,
      n: metrics.n ?? panel.test_sizes?.[String(year)]?.n,
      nPos: metrics.n_pos ?? panel.test_sizes?.[String(year)]?.n_pos,
      current,
      precision: metrics.precision,
      recall: metrics.recall,
      backward,
      trainSeconds: perYear?.[String(year)]?.train_seconds,
      scarce: year >= 2023,
    }
  })
})

const meanBackward = computed(() => props.result?.panel?.mean_f1_12y)
const meanCurrent = computed(() => {
  const values = rows.value.map((row) => row.current).filter((v) => Number.isFinite(Number(v)))
  if (!values.length) return null
  return values.reduce((sum, value) => sum + Number(value), 0) / values.length
})
</script>

<template>
  <div class="year-table-wrap">
    <table class="year-table">
      <thead>
        <tr>
          <th class="left">年份</th>
          <th>测试样本</th>
          <th>正样本</th>
          <th>当年 F1</th>
          <th>精确率</th>
          <th>召回率</th>
          <th>末年回评 F1</th>
          <th>训练耗时</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.year" :class="{ scarce: row.scarce }">
          <td class="left strong">{{ row.year }}</td>
          <td>{{ fmtInt(row.n) }}</td>
          <td>{{ fmtInt(row.nPos) }}</td>
          <td class="mono">{{ fmtF1(row.current) }}</td>
          <td class="mono">{{ fmtF1(row.precision) }}</td>
          <td class="mono">{{ fmtF1(row.recall) }}</td>
          <td class="mono strong">{{ fmtF1(row.backward) }}</td>
          <td class="mono muted">
            {{ row.trainSeconds === undefined || row.trainSeconds === null ? '-' : `${Number(row.trainSeconds).toFixed(1)} s` }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td class="left strong">12 年平均</td>
          <td colspan="2" class="muted">年度面板算术平均</td>
          <td class="mono strong">{{ meanCurrent === null ? '-' : fmtF1(meanCurrent) }}</td>
          <td colspan="2"></td>
          <td class="mono strong">{{ fmtF1(meanBackward) }}</td>
          <td class="muted">—</td>
        </tr>
      </tfoot>
    </table>
    <div class="year-table-note">
      2025 年测试分片仅 5 个正样本，当年与末年模型均未给出正判，F1 为 0；该读数按原样呈现，不作剔除。
    </div>
  </div>
</template>

<style scoped>
.year-table-wrap {
  width: 100%;
}

.year-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.4px;
  font-variant-numeric: tabular-nums;
}

.year-table th {
  padding: 5px 8px;
  text-align: right;
  font-weight: 600;
  font-size: 10.8px;
  letter-spacing: 0.3px;
  color: #5b6b80;
  background: #f7f9fc;
  border-bottom: 1px solid #e8edf5;
  white-space: nowrap;
}

.year-table td {
  padding: 2.2px 8px;
  text-align: right;
  border-bottom: 1px solid #f0f3f8;
  color: #26384d;
  white-space: nowrap;
}

.year-table .left {
  text-align: left;
}

.year-table tbody tr:nth-child(even) {
  background: #fbfcfe;
}

.year-table tbody tr.scarce {
  background: #fffaf0;
}

.year-table tfoot td {
  padding: 5px 8px;
  background: #f4f8fd;
  border-top: 1px solid #dbe6f3;
  font-size: 11.3px;
}

.year-table-note {
  margin-top: 5px;
  color: #8796aa;
  font-size: 10.6px;
  line-height: 1.45;
}
</style>
