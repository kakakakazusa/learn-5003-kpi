import { ref, watch } from 'vue'
import { api } from '../api'

// 各周期类型在趋势图中向前展示的周期数
export const PERIOD_LIMIT = { week: 12, month: 12, quarter: 4, halfyear: 4, year: 4 }

export function useDw() {
  // 元数据（组织维度不含 employee）
  const orgTypes = ref([])
  const periodTypes = ref([])
  const dimensions = ref({})
  const projects = ref([])

  // 部门看板（组织维度）
  const selectedOrgType = ref('department')
  const selectedPeriod = ref('month')
  const orgBoard = ref([])
  const orgLoading = ref(false)
  const orgError = ref('')

  // 项目看板（项目维度）
  const selectedProject = ref(null) // null 表示全部项目
  const projectPeriod = ref('month')
  const projectBoard = ref([])
  const projectLoading = ref(false)
  const projectError = ref('')

  async function loadMeta() {
    try {
      const data = await api.dwMeta()
      orgTypes.value = (data.org_types || []).filter((item) => item.value !== 'employee')
      periodTypes.value = data.period_types || []
      dimensions.value = data.dimensions || {}
    } catch (error) {
      // 元数据失败不阻断页面，筛选器回退为空
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
      projectBoard.value = await api.dwProjectBoard(projectPeriod.value)
    } catch (error) {
      projectError.value = error.message
      projectBoard.value = []
    } finally {
      projectLoading.value = false
    }
  }

  // 当前周期值（用于过滤未来周期，例如 2026-11 时不显示 2026-12）
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

  // 周期列表：去重 + 升序 + 过滤未来周期 + 截断最近 N 个
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
    projectLoading,
    projectError,
    loadProjectBoard,
    loadMeta,
    loadProjects,
    periodLabels,
  }
}
