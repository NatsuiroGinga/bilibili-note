<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  years: { type: Array, default: () => [] },
  backward: { type: Object, default: () => ({}) },
  current: { type: Object, default: () => ({}) },
  height: { type: Number, default: 300 },
})

const el = ref(null)
let chart = null
let observer = null

function valuesOf(source) {
  return props.years.map((year) => {
    const value = source?.[String(year)]
    return value === null || value === undefined ? null : Number(value)
  })
}

function render() {
  if (!chart) return
  const option = {
    animationDuration: 600,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#b7c6da', type: 'dashed' } },
      valueFormatter: (value) => (value === null || value === undefined ? '-' : Number(value).toFixed(4)),
    },
    legend: {
      right: 6,
      top: 0,
      itemWidth: 18,
      itemHeight: 3,
      textStyle: { color: '#5b6b80', fontSize: 11.5 },
      data: ['末年模型统一回评', '当年即时评价'],
    },
    grid: { left: 44, right: 20, top: 32, bottom: 26 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.years,
      axisLine: { lineStyle: { color: '#cfd9e6' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7c92', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      interval: 0.2,
      name: 'F1',
      nameTextStyle: { color: '#8a99ad', fontSize: 11, padding: [0, 0, 0, -30] },
      axisLabel: { color: '#6b7c92', fontSize: 11, formatter: (v) => v.toFixed(1) },
      splitLine: { lineStyle: { color: '#edf1f7', type: 'dashed' } },
    },
    series: [
      {
        name: '末年模型统一回评',
        type: 'line',
        data: valuesOf(props.backward),
        smooth: 0.22,
        symbol: 'circle',
        symbolSize: 5,
        showSymbol: true,
        lineStyle: { width: 2.4, color: '#1e5f96' },
        itemStyle: { color: '#1e5f96', borderColor: '#fff', borderWidth: 1 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(30, 95, 150, 0.18)' },
            { offset: 1, color: 'rgba(30, 95, 150, 0.01)' },
          ]),
        },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(208, 138, 28, 0.06)' },
          label: {
            show: true,
            position: 'insideTop',
            color: '#b07a1e',
            fontSize: 10.5,
            formatter: '稀缺年（2023–2025）',
          },
          data: [[{ xAxis: '2023' }, { xAxis: '2025' }]],
        },
      },
      {
        name: '当年即时评价',
        type: 'line',
        data: valuesOf(props.current),
        smooth: 0.22,
        symbol: 'diamond',
        symbolSize: 5,
        showSymbol: true,
        lineStyle: { width: 1.8, color: '#d08a1c', type: 'dashed' },
        itemStyle: { color: '#d08a1c', borderColor: '#fff', borderWidth: 1 },
      },
    ],
  }
  chart.setOption(option, true)
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(el.value)
})

watch(
  () => [props.years, props.backward, props.current],
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
