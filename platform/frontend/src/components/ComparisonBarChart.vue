<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  cells: { type: Object, default: () => ({}) },
  completed: { type: Array, default: () => [] },
  missing: { type: Array, default: () => [] },
  platform: { type: Object, default: null },
  reference: { type: Object, default: null },
  height: { type: Number, default: 310 },
})

const el = ref(null)
let chart = null
let observer = null

const order = ['naive', 'naive_members', 'replay', 'full']
const labels = {
  naive: 'naive\n朴素预算',
  naive_members: 'naive_members\n朴素＋成员',
  replay: 'replay\n配额回放',
  full: 'full\n配额＋成员',
}

function render() {
  if (!chart) return
  const categories = order
  const cliData = order.map((cell) => {
    const row = props.cells?.[cell]
    return row && Number.isFinite(Number(row.mean_f1_12y)) ? Number(row.mean_f1_12y) : null
  })
  const missingPoints = (props.missing || []).map((cell) => ({
    coord: [cell, 0],
    value: '训练中',
    symbol: 'rect',
    symbolSize: [64, 21],
    symbolOffset: [0, -13],
    itemStyle: { color: '#fff8ec', borderColor: '#f0ddb9', borderWidth: 1 },
    label: { formatter: '训练中', color: '#b07a1e', fontSize: 10.5, fontWeight: 600 },
  }))
  const platformData =
    props.platform && Number.isFinite(Number(props.platform.mean_f1_12y))
      ? [{ value: [props.platform.cell || 'naive', Number(props.platform.mean_f1_12y)] }]
      : []
  const referenceLine = props.reference && Number.isFinite(Number(props.reference.mean_f1_12y))
    ? {
        symbol: 'none',
        silent: true,
        lineStyle: { color: '#8a6bbf', type: 'dashed', width: 1.2 },
        label: {
          formatter: `full 先导参考 ${Number(props.reference.mean_f1_12y).toFixed(4)}（非平台复刻）`,
          position: 'insideEndTop',
          color: '#7a5aa8',
          fontSize: 10.5,
        },
        data: [{ yAxis: Number(props.reference.mean_f1_12y) }],
      }
    : undefined

  chart.setOption(
    {
      animationDuration: 650,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(30, 95, 150, 0.05)' } },
        valueFormatter: (value) => (value === null || value === undefined ? '-' : Number(value).toFixed(4)),
      },
      legend: {
        right: 8,
        top: 0,
        itemWidth: 13,
        itemHeight: 9,
        textStyle: { color: '#5b6b80', fontSize: 11.5 },
        data: ['CLI 四格收据', '平台 E2E 收据'],
      },
      grid: { left: 52, right: 26, top: 34, bottom: 44 },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: { lineStyle: { color: '#cfd9e6' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#5b6b80',
          fontSize: 10.8,
          lineHeight: 15,
          formatter: (value) => labels[value] || value,
        },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 1,
        interval: 0.2,
        name: '12 年平均 F1',
        nameTextStyle: { color: '#8a99ad', fontSize: 11, padding: [0, 0, 4, 0] },
        axisLabel: { color: '#6b7c92', fontSize: 11, formatter: (v) => v.toFixed(1) },
        splitLine: { lineStyle: { color: '#edf1f7', type: 'dashed' } },
      },
      series: [
        {
          name: 'CLI 四格收据',
          type: 'bar',
          barWidth: 44,
          data: cliData,
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#4d86bf' },
              { offset: 1, color: '#28649c' },
            ]),
          },
          label: {
            show: true,
            position: 'top',
            formatter: (params) =>
              params.value === null || params.value === undefined ? '' : Number(params.value).toFixed(4),
            color: '#1e5f96',
            fontSize: 11,
            fontWeight: 600,
          },
          markPoint: { data: missingPoints, silent: true },
          markLine: referenceLine,
        },
        {
          name: '平台 E2E 收据',
          type: 'scatter',
          symbol: 'diamond',
          symbolSize: 13,
          data: platformData,
          itemStyle: { color: '#1f9d63', borderColor: '#fff', borderWidth: 1.5 },
          label: {
            show: true,
            position: 'right',
            formatter: (params) => `平台 ${Number(params.value?.[1]).toFixed(4)}`,
            color: '#1c7c52',
            fontSize: 10.5,
            fontWeight: 600,
          },
          z: 5,
        },
      ],
    },
    true,
  )
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(el.value)
})

watch(
  () => [props.cells, props.completed, props.missing, props.platform, props.reference],
  () => render(),
  { deep: true },
)

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="el" class="chart" :style="{ height: `${height}px` }"></div>
</template>
