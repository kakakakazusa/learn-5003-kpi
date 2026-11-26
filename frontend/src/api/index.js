// Use the Vite proxy (/api) in development and the same-origin Nginx reverse proxy in production
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch {
    throw new Error('Cannot connect to the backend service; make sure Flask is running')
  }

  const isJson = (res.headers.get('content-type') || '').includes('application/json')
  const body = isJson ? await res.json() : null

  if (!res.ok) {
    const fallback = res.status >= 500
      ? 'Backend service temporarily unavailable; make sure Flask is running'
      : `HTTP ${res.status}: ${res.statusText}`
    throw new Error(body?.message || fallback)
  }
  if (!body) {
    throw new Error('The API returned a non-JSON response; check the proxy or backend configuration')
  }
  if (body.code !== 0) {
    throw new Error(body.message || 'Request failed')
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
  // Warehouse: organization dimension (Department Board)
  dwMeta: () => request('/dw/meta'),
  dwBoard: (orgType, periodType) => request(`/dw/board?org_type=${encodeURIComponent(orgType)}&period_type=${encodeURIComponent(periodType)}`),
  dwClearCache: () => request('/dw/cache/clear', { method: 'POST' }),

  // Warehouse: project dimension (Project Board)
  dwProjectMeta: () => request('/dw/project/meta'),
  dwProjectBoard: (periodType) => request(`/dw/project/board?period_type=${encodeURIComponent(periodType)}`),
  dwProjectKpi: (params) => request(`/dw/project/kpi?${qs(params)}`),
  dwProjectEc: (params) => request(`/dw/project/ec?${qs(params)}`),
}
