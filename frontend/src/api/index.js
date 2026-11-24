// 开发期走 Vite 代理(/api)，生产期走 Nginx 同域反代
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch {
    throw new Error('无法连接后端服务，请确认 Flask 已启动')
  }

  const isJson = (res.headers.get('content-type') || '').includes('application/json')
  const body = isJson ? await res.json() : null

  if (!res.ok) {
    const fallback = res.status >= 500
      ? '后端服务暂不可用，请确认 Flask 已启动'
      : `HTTP ${res.status}: ${res.statusText}`
    throw new Error(body?.message || fallback)
  }
  if (!body) {
    throw new Error('接口返回了非 JSON 响应，请检查代理或后端配置')
  }
  if (body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
  return body.data
}

function qs(params) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')
}

export const api = {
  health: () => request('/health'),

  // 数仓库：组织维度（部门看板）
  dwMeta: () => request('/dw/meta'),
  dwBoard: (orgType, periodType) => request(`/dw/board?org_type=${encodeURIComponent(orgType)}&period_type=${encodeURIComponent(periodType)}`),
  dwClearCache: () => request('/dw/cache/clear', { method: 'POST' }),

  // 数仓库：项目维度（项目看板）
  dwProjectMeta: () => request('/dw/project/meta'),
  dwProjectBoard: (periodType) => request(`/dw/project/board?period_type=${encodeURIComponent(periodType)}`),
  dwProjectKpi: (params) => request(`/dw/project/kpi?${qs(params)}`),
}
