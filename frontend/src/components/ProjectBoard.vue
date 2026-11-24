<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { useDw } from '../composables/useDw'
import TrendChart from './TrendChart.vue'

const {
  periodTypes,
  projects,
  selectedProject,
  projectPeriod,
  projectBoard,
  projectEcBoard,
  projectLoading,
  projectError,
  loadProjectBoard,
  loadProjects,
  loadMeta,
  periodLabels,
} = useDw()

const FORMULAS = {
  completion: '需求完成率 = 需求完成数 ÷ 需求承接数 × 100%',
  on_time: '准时交付率 = 准时交付数 ÷ 应交付数 × 100%',
  ec_resolution: '故障解决率 = 故障解决数 ÷ 故障发现数 × 100%',
  ec_response: '平均响应时长 = 故障响应时长总和 ÷ 故障数（分钟）',
}

const detail = ref(null)

onMounted(() => {
  loadMeta()
  loadProjects()
})

const periods = computed(() => periodLabels(projectBoard.value, projectPeriod.value))
const ecPeriods = computed(() => periodLabels(projectEcBoard.value, projectPeriod.value))

function fmtPct(value) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

function findRow(period, projectId) {
  return projectBoard.value.find((item) => item.period_value === period && item.project_id === projectId)
}

function findEcRow(period, projectId) {
  return projectEcBoard.value.find((item) => item.period_value === period && item.project_id === projectId)
}

const completionSeries = computed(() => {
  if (selectedProject.value) {
    const rows = periods.value.map((p) => findRow(p, selectedProject.value))
    return [{ name: '需求完成率', data: rows.map((r) => r?.completion_rate ?? null), color: '#31866c' }]
  }
  const data = periods.value.map((p) => {
    const rows = projectBoard.value.filter((item) => item.period_value === p)
    const assign = rows.reduce((sum, item) => sum + (item.assign_cnt || 0), 0)
    const complete = rows.reduce((sum, item) => sum + (item.complete_cnt || 0), 0)
    return assign > 0 ? complete / assign : null
  })
  return [{ name: '需求完成率', data, color: '#31866c' }]
})

const onTimeSeries = computed(() => {
  if (selectedProject.value) {
    const rows = periods.value.map((p) => findRow(p, selectedProject.value))
    return [{ name: '准时交付率', data: rows.map((r) => r?.on_time_rate ?? null), color: '#e5a84b' }]
  }
  const data = periods.value.map((p) => {
    const rows = projectBoard.value.filter((item) => item.period_value === p)
    const complete = rows.reduce((sum, item) => sum + (item.complete_cnt || 0), 0)
    const weighted = rows.reduce((sum, item) => sum + ((item.on_time_rate || 0) * (item.complete_cnt || 0)), 0)
    return complete > 0 ? weighted / complete : null
  })
  return [{ name: '准时交付率', data, color: '#e5a84b' }]
})

const ecResolutionSeries = computed(() => {
  if (selectedProject.value) {
    const rows = ecPeriods.value.map((p) => findEcRow(p, selectedProject.value))
    return [{ name: '故障解决率', data: rows.map((r) => r?.resolution_rate ?? null), color: '#5e8fad' }]
  }
  const data = ecPeriods.value.map((p) => {
    const rows = projectEcBoard.value.filter((item) => item.period_value === p)
    const found = rows.reduce((sum, item) => sum + (item.found_cnt || 0), 0)
    const resolved = rows.reduce((sum, item) => sum + (item.resolved_cnt || 0), 0)
    return found > 0 ? resolved / found : null
  })
  return [{ name: '故障解决率', data, color: '#5e8fad' }]
})

const ecResponseSeries = computed(() => {
  if (selectedProject.value) {
    const rows = ecPeriods.value.map((p) => findEcRow(p, selectedProject.value))
    return [{ name: '平均响应时长', data: rows.map((r) => r?.avg_response_minutes ?? null), color: '#8d7aa8' }]
  }
  const data = ecPeriods.value.map((p) => {
    const rows = projectEcBoard.value.filter((item) => item.period_value === p)
    const found = rows.reduce((sum, item) => sum + (item.found_cnt || 0), 0)
    const respSum = rows.reduce((sum, item) => sum + (item.response_minutes_sum || 0), 0)
    return found > 0 ? respSum / found : null
  })
  return [{ name: '平均响应时长', data, color: '#8d7aa8' }]
})

function showDetail(kind, { seriesName, dataIndex }) {
  const period = periods.value[dataIndex]
  let rows = []
  if (kind === 'completion') {
    if (selectedProject.value) {
      const item = findRow(period, selectedProject.value)
      rows = [
        { label: '需求完成率', value: fmtPct(item?.completion_rate) },
        { label: '需求承接数', value: item?.assign_cnt ?? 0 },
        { label: '需求完成数', value: item?.complete_cnt ?? 0 },
      ]
    } else {
      const items = projectBoard.value.filter((row) => row.period_value === period)
      const assign = items.reduce((sum, row) => sum + (row.assign_cnt || 0), 0)
      const complete = items.reduce((sum, row) => sum + (row.complete_cnt || 0), 0)
      rows = [
        { label: '需求完成率', value: assign > 0 ? fmtPct(complete / assign) : '—' },
        { label: '需求承接数', value: assign },
        { label: '需求完成数', value: complete },
      ]
    }
  } else if (kind === 'on_time') {
    if (selectedProject.value) {
      const item = findRow(period, selectedProject.value)
      rows = [
        { label: '准时交付率', value: fmtPct(item?.on_time_rate) },
        { label: '应交付数', value: item?.due_cnt ?? 0 },
        { label: '准时交付数', value: item?.on_time_cnt ?? 0 },
      ]
    } else {
      const items = projectBoard.value.filter((row) => row.period_value === period)
      const due = items.reduce((sum, row) => sum + (row.due_cnt || 0), 0)
      const onTime = items.reduce((sum, row) => sum + (row.on_time_cnt || 0), 0)
      rows = [
        { label: '准时交付率', value: due > 0 ? fmtPct(onTime / due) : '—' },
        { label: '应交付数', value: due },
        { label: '准时交付数', value: onTime },
      ]
    }
  } else if (kind === 'ec_resolution') {
    const ecPeriod = ecPeriods.value[dataIndex]
    if (selectedProject.value) {
      const item = findEcRow(ecPeriod, selectedProject.value)
      rows = [
        { label: '故障解决率', value: fmtPct(item?.resolution_rate) },
        { label: '故障发现数', value: item?.found_cnt ?? 0 },
        { label: '故障解决数', value: item?.resolved_cnt ?? 0 },
      ]
    } else {
      const items = projectEcBoard.value.filter((row) => row.period_value === ecPeriod)
      const found = items.reduce((sum, row) => sum + (row.found_cnt || 0), 0)
      const resolved = items.reduce((sum, row) => sum + (row.resolved_cnt || 0), 0)
      rows = [
        { label: '故障解决率', value: found > 0 ? fmtPct(resolved / found) : '—' },
        { label: '故障发现数', value: found },
        { label: '故障解决数', value: resolved },
      ]
    }
  } else if (kind === 'ec_response') {
    const ecPeriod = ecPeriods.value[dataIndex]
    if (selectedProject.value) {
      const item = findEcRow(ecPeriod, selectedProject.value)
      rows = [
        { label: '平均响应时长', value: item?.avg_response_minutes == null ? '—' : `${item.avg_response_minutes} 分钟` },
        { label: '响应时长总和', value: `${item?.response_minutes_sum ?? 0} 分钟` },
        { label: '故障数', value: item?.found_cnt ?? 0 },
      ]
    } else {
      const items = projectEcBoard.value.filter((row) => row.period_value === ecPeriod)
      const found = items.reduce((sum, row) => sum + (row.found_cnt || 0), 0)
      const respSum = items.reduce((sum, row) => sum + (row.response_minutes_sum || 0), 0)
      rows = [
        { label: '平均响应时长', value: found > 0 ? `${(respSum / found).toFixed(1)} 分钟` : '—' },
        { label: '响应时长总和', value: `${respSum} 分钟` },
        { label: '故障数', value: found },
      ]
    }
  }
  detail.value = { title: `${seriesName} · ${period}`, rows }
}

async function refreshCache() {
  try {
    await api.dwClearCache()
  } catch {
    // 清缓存失败时仍尝试重新取数
  }
  loadProjectBoard()
}
</script>

<template>
  <section class="board">
    <div class="range-row" aria-label="项目看板筛选">
      <div class="board-filters">
        <label class="range-select-wrap">
          <span>项目</span>
          <select v-model="selectedProject" class="range-select scope-select" aria-label="项目">
            <option :value="null">全部项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
          </select>
        </label>
        <label class="range-select-wrap">
          <span>时间</span>
          <select v-model="projectPeriod" class="range-select" aria-label="时间周期">
            <option v-for="type in periodTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
          </select>
        </label>
      </div>
      <button class="refresh-button" type="button" :disabled="projectLoading" @click="refreshCache">
        <svg :class="{ spinning: projectLoading }" viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 8A6.5 6.5 0 0 0 5 5.5L3.5 7M3.5 7V3.5M3.5 7H7m-3.5 5A6.5 6.5 0 0 0 15 14.5l1.5-1.5m0 0v3.5m0-3.5H13" /></svg>
        刷新缓存
      </button>
    </div>

    <div v-if="projectError" class="error-banner" role="alert">
      <div><strong>暂时无法加载项目看板</strong><p>{{ projectError }}</p></div>
      <button type="button" @click="loadProjectBoard">重试</button>
    </div>

    <div class="trend-list" :aria-busy="projectLoading">
      <TrendChart title="需求完成率" subtitle="项目需求完成情况" :formula="FORMULAS.completion" :x-labels="periods" :series="completionSeries" percent @point-click="(p) => showDetail('completion', p)" />
      <TrendChart title="准时交付率" subtitle="项目需求准时交付情况" :formula="FORMULAS.on_time" :x-labels="periods" :series="onTimeSeries" percent @point-click="(p) => showDetail('on_time', p)" />
      <TrendChart title="EC 故障解决率" subtitle="项目故障解决情况" :formula="FORMULAS.ec_resolution" :x-labels="ecPeriods" :series="ecResolutionSeries" percent @point-click="(p) => showDetail('ec_resolution', p)" />
      <TrendChart title="EC 平均响应时长" subtitle="项目故障响应情况" :formula="FORMULAS.ec_response" :x-labels="ecPeriods" :series="ecResponseSeries" unit=" 分钟" @point-click="(p) => showDetail('ec_response', p)" />
    </div>

    <div v-if="detail" class="detail-mask" @click.self="detail = null">
      <div class="detail-panel" role="dialog" aria-label="指标明细">
        <div class="detail-head">
          <strong>{{ detail.title }}</strong>
          <button type="button" class="detail-close" aria-label="关闭" @click="detail = null">×</button>
        </div>
        <div class="detail-body">
          <div v-for="row in detail.rows" :key="row.label" class="detail-row">
            <span>{{ row.label }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
