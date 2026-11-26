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
  completion: 'Completion Rate = Requirements Completed / Requirements Assigned x 100%',
  on_time: 'On-time Rate = On-time Deliveries / Requirements Due x 100%',
  ec_resolution: 'Resolution Rate = Incidents Resolved / Incidents Found x 100%',
  ec_response: 'Avg. Response Time = Total Response Minutes / Incidents (min)',
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
    return [{ name: 'Requirement Completion Rate', data: rows.map((r) => r?.completion_rate ?? null), color: '#31866c' }]
  }
  const data = periods.value.map((p) => {
    const rows = projectBoard.value.filter((item) => item.period_value === p)
    const assign = rows.reduce((sum, item) => sum + (item.assign_cnt || 0), 0)
    const complete = rows.reduce((sum, item) => sum + (item.complete_cnt || 0), 0)
    return assign > 0 ? complete / assign : null
  })
  return [{ name: 'Requirement Completion Rate', data, color: '#31866c' }]
})

const onTimeSeries = computed(() => {
  if (selectedProject.value) {
    const rows = periods.value.map((p) => findRow(p, selectedProject.value))
    return [{ name: 'On-time Delivery Rate', data: rows.map((r) => r?.on_time_rate ?? null), color: '#e5a84b' }]
  }
  const data = periods.value.map((p) => {
    const rows = projectBoard.value.filter((item) => item.period_value === p)
    const complete = rows.reduce((sum, item) => sum + (item.complete_cnt || 0), 0)
    const weighted = rows.reduce((sum, item) => sum + ((item.on_time_rate || 0) * (item.complete_cnt || 0)), 0)
    return complete > 0 ? weighted / complete : null
  })
  return [{ name: 'On-time Delivery Rate', data, color: '#e5a84b' }]
})

const ecResolutionSeries = computed(() => {
  if (selectedProject.value) {
    const rows = ecPeriods.value.map((p) => findEcRow(p, selectedProject.value))
    return [{ name: 'Incident Resolution Rate', data: rows.map((r) => r?.resolution_rate ?? null), color: '#5e8fad' }]
  }
  const data = ecPeriods.value.map((p) => {
    const rows = projectEcBoard.value.filter((item) => item.period_value === p)
    const found = rows.reduce((sum, item) => sum + (item.found_cnt || 0), 0)
    const resolved = rows.reduce((sum, item) => sum + (item.resolved_cnt || 0), 0)
    return found > 0 ? resolved / found : null
  })
  return [{ name: 'Incident Resolution Rate', data, color: '#5e8fad' }]
})

const ecResponseSeries = computed(() => {
  if (selectedProject.value) {
    const rows = ecPeriods.value.map((p) => findEcRow(p, selectedProject.value))
    return [{ name: 'Avg. Response Time', data: rows.map((r) => r?.avg_response_minutes ?? null), color: '#8d7aa8' }]
  }
  const data = ecPeriods.value.map((p) => {
    const rows = projectEcBoard.value.filter((item) => item.period_value === p)
    const found = rows.reduce((sum, item) => sum + (item.found_cnt || 0), 0)
    const respSum = rows.reduce((sum, item) => sum + (item.response_minutes_sum || 0), 0)
    return found > 0 ? respSum / found : null
  })
  return [{ name: 'Avg. Response Time', data, color: '#8d7aa8' }]
})

function showDetail(kind, { seriesName, dataIndex }) {
  const period = periods.value[dataIndex]
  let rows = []
  if (kind === 'completion') {
    if (selectedProject.value) {
      const item = findRow(period, selectedProject.value)
      rows = [
        { label: 'Requirement Completion Rate', value: fmtPct(item?.completion_rate) },
        { label: 'Requirements Assigned', value: item?.assign_cnt ?? 0 },
        { label: 'Requirements Completed', value: item?.complete_cnt ?? 0 },
      ]
    } else {
      const items = projectBoard.value.filter((row) => row.period_value === period)
      const assign = items.reduce((sum, row) => sum + (row.assign_cnt || 0), 0)
      const complete = items.reduce((sum, row) => sum + (row.complete_cnt || 0), 0)
      rows = [
        { label: 'Requirement Completion Rate', value: assign > 0 ? fmtPct(complete / assign) : '—' },
        { label: 'Requirements Assigned', value: assign },
        { label: 'Requirements Completed', value: complete },
      ]
    }
  } else if (kind === 'on_time') {
    if (selectedProject.value) {
      const item = findRow(period, selectedProject.value)
      rows = [
        { label: 'On-time Delivery Rate', value: fmtPct(item?.on_time_rate) },
        { label: 'Requirements Due', value: item?.due_cnt ?? 0 },
        { label: 'On-time Deliveries', value: item?.on_time_cnt ?? 0 },
      ]
    } else {
      const items = projectBoard.value.filter((row) => row.period_value === period)
      const due = items.reduce((sum, row) => sum + (row.due_cnt || 0), 0)
      const onTime = items.reduce((sum, row) => sum + (row.on_time_cnt || 0), 0)
      rows = [
        { label: 'On-time Delivery Rate', value: due > 0 ? fmtPct(onTime / due) : '—' },
        { label: 'Requirements Due', value: due },
        { label: 'On-time Deliveries', value: onTime },
      ]
    }
  } else if (kind === 'ec_resolution') {
    const ecPeriod = ecPeriods.value[dataIndex]
    if (selectedProject.value) {
      const item = findEcRow(ecPeriod, selectedProject.value)
      rows = [
        { label: 'Incident Resolution Rate', value: fmtPct(item?.resolution_rate) },
        { label: 'Incidents Found', value: item?.found_cnt ?? 0 },
        { label: 'Incidents Resolved', value: item?.resolved_cnt ?? 0 },
      ]
    } else {
      const items = projectEcBoard.value.filter((row) => row.period_value === ecPeriod)
      const found = items.reduce((sum, row) => sum + (row.found_cnt || 0), 0)
      const resolved = items.reduce((sum, row) => sum + (row.resolved_cnt || 0), 0)
      rows = [
        { label: 'Incident Resolution Rate', value: found > 0 ? fmtPct(resolved / found) : '—' },
        { label: 'Incidents Found', value: found },
        { label: 'Incidents Resolved', value: resolved },
      ]
    }
  } else if (kind === 'ec_response') {
    const ecPeriod = ecPeriods.value[dataIndex]
    if (selectedProject.value) {
      const item = findEcRow(ecPeriod, selectedProject.value)
      rows = [
        { label: 'Avg. Response Time', value: item?.avg_response_minutes == null ? '—' : `${item.avg_response_minutes} min` },
        { label: 'Total Response Time', value: `${item?.response_minutes_sum ?? 0} min` },
        { label: 'Incidents', value: item?.found_cnt ?? 0 },
      ]
    } else {
      const items = projectEcBoard.value.filter((row) => row.period_value === ecPeriod)
      const found = items.reduce((sum, row) => sum + (row.found_cnt || 0), 0)
      const respSum = items.reduce((sum, row) => sum + (row.response_minutes_sum || 0), 0)
      rows = [
        { label: 'Avg. Response Time', value: found > 0 ? `${(respSum / found).toFixed(1)} min` : '—' },
        { label: 'Total Response Time', value: `${respSum} min` },
        { label: 'Incidents', value: found },
      ]
    }
  }
  detail.value = { title: `${seriesName} · ${period}`, rows }
}

async function refreshCache() {
  try {
    await api.dwClearCache()
  } catch {
    // Still try to reload data if clearing the cache fails
  }
  loadProjectBoard()
}
</script>

<template>
  <section class="board">
    <div class="range-row" aria-label="Project Board filters">
      <div class="board-filters">
        <label class="range-select-wrap">
          <span>Project</span>
          <select v-model="selectedProject" class="range-select scope-select" aria-label="Project">
            <option :value="null">All Projects</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
          </select>
        </label>
        <label class="range-select-wrap">
          <span>Period</span>
          <select v-model="projectPeriod" class="range-select" aria-label="Period">
            <option v-for="type in periodTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
          </select>
        </label>
      </div>
      <button class="refresh-button" type="button" :disabled="projectLoading" @click="refreshCache">
        <svg :class="{ spinning: projectLoading }" viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 8A6.5 6.5 0 0 0 5 5.5L3.5 7M3.5 7V3.5M3.5 7H7m-3.5 5A6.5 6.5 0 0 0 15 14.5l1.5-1.5m0 0v3.5m0-3.5H13" /></svg>
        Clear Cache
      </button>
    </div>

    <div v-if="projectError" class="error-banner" role="alert">
      <div><strong>Unable to load the Project Board</strong><p>{{ projectError }}</p></div>
      <button type="button" @click="loadProjectBoard">Retry</button>
    </div>

    <div class="trend-list" :aria-busy="projectLoading">
      <TrendChart title="Requirement Completion Rate" subtitle="Completion by project" :formula="FORMULAS.completion" :x-labels="periods" :series="completionSeries" percent @point-click="(p) => showDetail('completion', p)" />
      <TrendChart title="On-time Delivery Rate" subtitle="On-time delivery by project" :formula="FORMULAS.on_time" :x-labels="periods" :series="onTimeSeries" percent @point-click="(p) => showDetail('on_time', p)" />
      <TrendChart title="EC Resolution Rate" subtitle="Incident resolution by project" :formula="FORMULAS.ec_resolution" :x-labels="ecPeriods" :series="ecResolutionSeries" percent @point-click="(p) => showDetail('ec_resolution', p)" />
      <TrendChart title="EC Avg. Response Time" subtitle="Incident response by project" :formula="FORMULAS.ec_response" :x-labels="ecPeriods" :series="ecResponseSeries" unit=" min" @point-click="(p) => showDetail('ec_response', p)" />
    </div>

    <div v-if="detail" class="detail-mask" @click.self="detail = null">
      <div class="detail-panel" role="dialog" aria-label="Metric Details">
        <div class="detail-head">
          <strong>{{ detail.title }}</strong>
          <button type="button" class="detail-close" aria-label="Close" @click="detail = null">×</button>
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
