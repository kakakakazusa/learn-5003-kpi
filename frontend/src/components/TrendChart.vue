<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  formula: { type: String, default: '' },
  xLabels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  unit: { type: String, default: '' },
  percent: { type: Boolean, default: false },
})

const emit = defineEmits(['point-click'])

const chartElement = ref(null)
let chart

function render() {
  if (!chart) return
  const series = props.series.map((item) => ({
    name: item.name,
    type: item.type || 'line',
    smooth: true,
    showSymbol: false,
    data: item.data,
    yAxisIndex: item.yAxisIndex || 0,
    lineStyle: { width: 2.5, color: item.color },
    itemStyle: { color: item.color },
    ...(item.type === 'bar' ? { barMaxWidth: 18, itemStyle: { color: item.color, borderRadius: [4, 4, 0, 0] } } : {}),
  }))

  chart.setOption({
    animationDuration: 600,
    textStyle: { fontFamily: 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif' },
    legend: {
      top: 0,
      right: 30,
      itemWidth: 10,
      itemHeight: 8,
      textStyle: { color: '#7d8983', fontSize: 11 },
    },
    grid: { left: 8, right: 16, top: 34, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#18231f',
      borderWidth: 0,
      textStyle: { color: '#f5f7f5', fontSize: 12 },
      axisPointer: { type: 'line', lineStyle: { color: '#cbd8d0', type: 'dashed' } },
      formatter: (params) => {
        const rows = params.map((item) => {
          const value = props.percent
            ? `${Number(item.value * 100).toFixed(1)}%`
            : `${Number(item.value).toLocaleString('en-US')}${props.unit}`
          return `${item.marker}${item.seriesName}: ${value}`
        })
        return [params[0]?.axisValueLabel, ...rows].join('<br/>')
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: props.xLabels,
      axisLine: { lineStyle: { color: '#edf0ed' } },
      axisTick: { show: false },
      axisLabel: { color: '#939d97', fontSize: 10, hideOverlap: true },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: '#939d97',
        fontSize: 10,
        formatter: props.percent ? (value) => `${Math.round(value * 100)}%` : undefined,
      },
      splitLine: { lineStyle: { color: '#f0f2f0', type: 'dashed' } },
    },
    series,
  }, true)
}

function onClick(params) {
  emit('point-click', {
    seriesName: params.seriesName,
    dataIndex: params.dataIndex,
    xLabel: params.name,
  })
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  if (chartElement.value) {
    chart = echarts.init(chartElement.value)
    chart.on('click', onClick)
    render()
    window.addEventListener('resize', resize)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})

watch(() => [props.xLabels, props.series], render, { deep: true })
</script>

<template>
  <article class="panel trend-row">
    <div class="panel-heading">
      <div><h2>{{ title }}</h2><p>{{ subtitle }}</p></div>
      <span v-if="formula" class="help-wrap">
        <button class="help-button" type="button" aria-label="View metric formula">?</button>
        <span class="help-tip">{{ formula }}</span>
      </span>
    </div>
    <div ref="chartElement" class="trend-chart" role="img" :aria-label="title"></div>
  </article>
</template>
