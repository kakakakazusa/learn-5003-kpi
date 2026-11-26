import { ref, watch } from 'vue'
import { api } from '../api'

// Number of periods shown in the trend chart for each period type
export const PERIOD_LIMIT = { week: 12, month: 12, quarter: 4, halfyear: 4, year: 4 }

export function useDw() {
  // Metadata (the organization dimension excludes employee)
  const orgTypes = ref([])
  const periodTypes = ref([])
  const dimensions = ref({})
  const projects = ref([])

  // Department Board (organization dimension)
  const selectedOrgType = ref('department')
  const selectedPeriod = ref('month')
  const orgBoard = ref([])
  const orgLoading = ref(false)
  const orgError = ref('')

  // Project Board (project dimension)
  const selectedProject = ref(null) // null means All Projects
  const projectPeriod = ref('month')
  const projectBoard = ref([])
  const projectLoading = ref(false)
  const projectError = ref('')
  const projectEcBoard = ref([])

  async function loadMeta() {
    try {
      const data = await api.dwMeta()
      orgTypes.value = (data.org_types || []).filter((item) => item.value !== 'employee')
      periodTypes.value = data.period_types || []
      dimensions.value = data.dimensions || {}
    } catch (error) {
      // A metadata failure does not block the page; filters fall back to empty
      orgTypes.value = []
      periodTypes.value = []
      dimensions.value = {}
    }
  }

  async function loadProjects() {
    try {
      projects.value = await api.dwProjectMeta()
    } catch {
      projects.value = []
    }
  }

  async function loadOrgBoard() {
    orgLoading.value = true
    orgError.value = ''
    try {
      orgBoard.value = await api.dwBoard(selectedOrgType.value, selectedPeriod.value)
    } catch (error) {
      orgError.value = error.message
      orgBoard.value = []
    } finally {
      orgLoading.value = false
    }
  }

  async function loadProjectBoard() {
    projectLoading.value = true
    projectError.value = ''
    try {
      const [prData, ecData] = await Promise.all([
        api.dwProjectBoard(projectPeriod.value),
        api.dwProjectEc({ period_type: projectPeriod.value }),
      ])
      projectBoard.value = prData
      projectEcBoard.value = ecData
    } catch (error) {
      projectError.value = error.message
      projectBoard.value = []
      projectEcBoard.value = []
    } finally {
      projectLoading.value = false
    }
  }

  // Current period value (used to filter out future periods, e.g. do not show 2026-12 at 2026-11)
  function currentPeriodValue(periodType) {
    const now = new Date()
    const y = now.getFullYear()
    const m = now.getMonth() + 1
    if (periodType === 'year') return String(y)
    if (periodType === 'month') return `${y}-${String(m).padStart(2, '0')}`
    if (periodType === 'quarter') return `${y}-Q${Math.ceil(m / 3)}`
    if (periodType === 'halfyear') return `${y}-H${m <= 6 ? 1 : 2}`
    if (periodType === 'week') {
      const d = new Date(Date.UTC(y, now.getMonth(), now.getDate()))
      const dayNum = d.getUTCDay() || 7
      d.setUTCDate(d.getUTCDate() + 4 - dayNum)
      const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
      const week = Math.ceil((((d - yearStart) / 86400000) + 1) / 7)
      return `${d.getUTCFullYear()}-W${String(week).padStart(2, '0')}`
    }
    return ''
  }

  // Period list: dedupe + ascending sort + filter out future periods + keep the latest N
  function periodLabels(items, periodType) {
    const current = currentPeriodValue(periodType)
    const values = [...new Set(items.map((item) => item.period_value))]
      .filter((value) => !current || value <= current)
      .sort()
    const limit = PERIOD_LIMIT[periodType] || 12
    return values.slice(-limit)
  }

  watch([selectedOrgType, selectedPeriod], loadOrgBoard, { immediate: true })
  watch(projectPeriod, loadProjectBoard, { immediate: true })

  return {
    orgTypes,
    periodTypes,
    dimensions,
    projects,
    selectedOrgType,
    selectedPeriod,
    orgBoard,
    orgLoading,
    orgError,
    loadOrgBoard,
    selectedProject,
    projectPeriod,
    projectBoard,
    projectEcBoard,
    projectLoading,
    projectError,
    loadProjectBoard,
    loadMeta,
    loadProjects,
    periodLabels,
  }
}
