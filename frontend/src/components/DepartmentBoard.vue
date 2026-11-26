<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { useDw } from '../composables/useDw'
import TrendChart from './TrendChart.vue'

const {
  orgTypes,
  periodTypes,
  selectedOrgType,
  selectedPeriod,
  orgBoard,
  orgLoading,
  orgError,
  loadOrgBoard,
  loadMeta,
  periodLabels,
} = useDw()

const COLORS = ['#31866c', '#e5a84b', '#5e8fad', '#8d7aa8', '#c18b3d', '#4d9674', '#d58a5f', '#82a8bf']

const FORMULAS = {
  pr_completion: 'Completion Rate = Requirements Completed / Requirements Assigned x 100%',
  pr_ontime: 'On-time Rate = On-time Deliveries / Requirements Due x 100%',
  ec_resolution: 'Resolution Rate = Incidents Resolved / Incidents Found x 100%',
  ec_response: 'Avg. Response Time = Total Response Minutes / Incidents (min)',
}

const detail = ref(null)

onMounted(loadMeta)

const periods = computed(() => periodLabels(orgBoard.value, selectedPeriod.value))
const orgIds = computed(() => [...new Set(orgBoard.value.map((item) => item.org_id))])

function orgName(id) {
  return orgBoard.value.find((item) => item.org_id === id)?.org_name || String(id)
}

function colorAt(index) {
  return COLORS[index % COLORS.length]
}

const prCompletionSeries = computed(() => orgIds.value.map((id, index) => ({
  name: orgName(id),
  data: periods.value.map((p) => {
    const row = orgBoard.value.find((item) => item.period_value === p && item.org_id === id)
    return row?.pr?.completion_rate ?? null
  }),
  color: colorAt(index),
})))

const prOnTimeSeries = computed(() => orgIds.value.map((id, index) => ({
  name: orgName(id),
  data: periods.value.map((p) => {
    const row = orgBoard.value.find((item) => item.period_value === p && item.org_id === id)
    return row?.pr?.on_time_rate ?? null
  }),
  color: colorAt(index),
})))

const ecResolutionSeries = computed(() => orgIds.value.map((id, index) => ({
  name: orgName(id),
  data: periods.value.map((p) => {
    const row = orgBoard.value.find((item) => item.period_value === p && item.org_id === id)
    return row?.ec?.resolution_rate ?? null
  }),
  color: colorAt(index),
})))

const ecResponseSeries = computed(() => orgIds.value.map((id, index) => ({
  name: orgName(id),
  data: periods.value.map((p) => {
    const row = orgBoard.value.find((item) => item.period_value === p && item.org_id === id)
    return row?.ec?.avg_response_minutes ?? null
  }),
  color: colorAt(index),
})))

function fmtPct(value) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

function showDetail(kind, { seriesName, dataIndex }) {
  const period = periods.value[dataIndex]
  const item = orgBoard.value.find((row) => row.period_value === period && row.org_name === seriesName)
  if (!item) return
  const pr = item.pr || {}
  const ec = item.ec || {}
  let rows = []
  if (kind === 'pr_completion') {
    rows = [
      { label: 'Requirement Completion Rate', value: fmtPct(pr.completion_rate) },
      { label: 'Requirements Assigned', value: pr.assign_cnt ?? 0 },
      { label: 'Requirements Completed', value: pr.complete_cnt ?? 0 },
    ]
  } else if (kind === 'pr_ontime') {
    rows = [
      { label: 'On-time Delivery Rate', value: fmtPct(pr.on_time_rate) },
      { label: 'Requirements Due', value: pr.due_cnt ?? 0 },
      { label: 'On-time Deliveries', value: pr.on_time_cnt ?? 0 },
    ]
  } else if (kind === 'ec_resolution') {
    rows = [
      { label: 'Incident Resolution Rate', value: fmtPct(ec.resolution_rate) },
      { label: 'Incidents Found', value: ec.found_cnt ?? 0 },
      { label: 'Incidents Resolved', value: ec.resolved_cnt ?? 0 },
    ]
  } else if (kind === 'ec_response') {
    rows = [
      { label: 'Avg. Response Time', value: ec.avg_response_minutes == null ? '—' : `${ec.avg_response_minutes} min` },
      { label: 'Total Response Time', value: `${ec.response_minutes_sum ?? 0} min` },
      { label: 'Incidents', value: ec.found_cnt ?? 0 },
    ]
  }
  detail.value = { title: `${seriesName} · ${period}`, rows }
}

async function refreshCache() {
  try {
    await api.dwClearCache()
  } catch {
    // Still try to reload data if clearing the cache fails
  }
  loadOrgBoard()
}
</script>

<template>
  <section class="board">
    <div class="range-row" aria-label="Department Board filters">
      <div class="board-filters">
        <label class="range-select-wrap">
          <span>Organization dimension</span>
          <select v-model="selectedOrgType" class="range-select scope-select" aria-label="Organization dimension">
            <option v-for="type in orgTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
          </select>
        </label>
        <label class="range-select-wrap">
          <span>Period</span>
          <select v-model="selectedPeriod" class="range-select" aria-label="Period">
            <option v-for="type in periodTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
          </select>
        </label>
      </div>
      <button class="refresh-button" type="button" :disabled="orgLoading" @click="refreshCache">
        <svg :class="{ spinning: orgLoading }" viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 8A6.5 6.5 0 0 0 5 5.5L3.5 7M3.5 7V3.5M3.5 7H7m-3.5 5A6.5 6.5 0 0 0 15 14.5l1.5-1.5m0 0v3.5m0-3.5H13" /></svg>
        Clear Cache
      </button>
    </div>

    <div v-if="orgError" class="error-banner" role="alert">
      <div><strong>Unable to load the Department Board</strong><p>{{ orgError }}</p></div>
      <button type="button" @click="loadOrgBoard">Retry</button>
    </div>

    <div class="trend-list" :aria-busy="orgLoading">
      <TrendChart title="PR Completion Rate" :subtitle="`By ${orgTypes.find((item) => item.value === selectedOrgType)?.label || 'Organization'}`" :formula="FORMULAS.pr_completion" :x-labels="periods" :series="prCompletionSeries" percent @point-click="(p) => showDetail('pr_completion', p)" />
      <TrendChart title="PR On-time Delivery Rate" subtitle="By Organization" :formula="FORMULAS.pr_ontime" :x-labels="periods" :series="prOnTimeSeries" percent @point-click="(p) => showDetail('pr_ontime', p)" />
      <TrendChart title="EC Resolution Rate" subtitle="By Organization" :formula="FORMULAS.ec_resolution" :x-labels="periods" :series="ecResolutionSeries" percent @point-click="(p) => showDetail('ec_resolution', p)" />
      <TrendChart title="EC Avg. Response Time" subtitle="By Organization" :formula="FORMULAS.ec_response" :x-labels="periods" :series="ecResponseSeries" unit=" min" @point-click="(p) => showDetail('ec_response', p)" />
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
