import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods (MVP endpoints)
export const creativeAPI = {
  // Upload video (MVP)
  uploadVideo: (formData) => api.post('/api/v1/creative/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),

  // Get all creatives
  getCreatives: (params) => api.get('/api/v1/creative/creatives', { params }),

  // Analyze creative
  analyzeCreative: (data) => api.post('/api/v1/creative/analyze', data),

  // Update creative metrics (MVP)
  updateCreative: (id, data) => {
    const formData = new FormData()
    formData.append('impressions', data.impressions || 0)
    formData.append('clicks', data.clicks || 0)
    formData.append('conversions', data.conversions || 0)
    return api.put(`/api/v1/creative/creatives/${id}/metrics`, formData)
  },

  // Get top patterns
  getTopPatterns: (params) => api.get('/api/v1/creative/patterns/top', { params }),

  // Get pattern recommendations (Thompson Sampling)
  getNextPatterns: (params) => api.get('/api/v1/creative/recommend/next-patterns', { params }),

  // Get scaling recommendations
  getScalingRecommendations: (data) => api.post('/api/v1/creative/recommend/scaling', data),

  // Analyze early signals (24-72h)
  analyzeEarlySignals: (creativeId) => api.post('/api/v1/creative/analyze-early-signals', {
    creative_id: creativeId,
  }),

  // Bulk analyze early signals
  bulkAnalyzeEarlySignals: (creativeIds) => api.post('/api/v1/creative/bulk-analyze-24h', {
    creative_ids: creativeIds,
  }),

  // Get model metrics
  getModelMetrics: () => api.get('/api/v1/creative/models/metrics'),

  // Auto-train models
  autoTrainModels: () => api.post('/api/v1/creative/models/auto-train'),

  // Update from UTM
  updateFromUTM: (data) => api.post('/api/v1/creative/update-from-utm', data),

  // Bulk update from UTM
  bulkUpdateFromUTM: (campaigns) => api.post('/api/v1/creative/bulk-update-from-utm', {
    utm_campaigns: campaigns,
  }),
}

export const analyticsAPI = {
  // Get analytics
  getAnalytics: (params) => api.get('/api/v1/analytics', { params }),

  // Get funnel data
  getFunnel: (params) => api.get('/api/v1/analytics/funnel', { params }),
}

export default api
