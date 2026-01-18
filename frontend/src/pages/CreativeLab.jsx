import { useState, useEffect } from 'react'
import { Video, Upload, TrendingUp, AlertCircle, CheckCircle, Clock, Sparkles, Trash2 } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'https://web-production-6cbde.up.railway.app'

const CreativeLab = () => {
  const [creatives, setCreatives] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, testing, significant, scale
  const [analyzingId, setAnalyzingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    fetchCreatives()
  }, [])

  const fetchCreatives = async () => {
    try {
      setLoading(true)
      const res = await axios.get(`${API_BASE}/api/v1/creative/creatives`)
      setCreatives(Array.isArray(res.data) ? res.data : [])
    } catch (error) {
      console.error('Failed to fetch creatives:', error)
      setCreatives([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async (creativeId) => {
    try {
      setAnalyzingId(creativeId)
      await axios.post(`${API_BASE}/api/v1/creative/creatives/${creativeId}/analyze`)
      // Refresh creatives list after analysis
      setTimeout(() => fetchCreatives(), 2000) // Wait 2s for analysis to complete
      alert('✅ Анализ завершен! Креатив обновлен.')
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('❌ Ошибка анализа. Проверьте что установлен ANTHROPIC_API_KEY.')
    } finally {
      setAnalyzingId(null)
    }
  }

  const handleDelete = async (creativeId, creativeName) => {
    if (!confirm(`Удалить креатив "${creativeName}"?`)) return

    try {
      setDeletingId(creativeId)
      await axios.delete(`${API_BASE}/api/v1/creative/creatives/${creativeId}`)
      // Remove from local state
      setCreatives(creatives.filter(c => c.id !== creativeId))
      alert('✅ Креатив удален')
    } catch (error) {
      console.error('Delete failed:', error)
      alert('❌ Ошибка удаления')
    } finally {
      setDeletingId(null)
    }
  }

  const getStatusBadge = (creative) => {
    const conversions = creative.conversions || 0
    const clicks = creative.clicks || 0
    const cvr = clicks > 0 ? (conversions / clicks) : 0

    if (conversions >= 10 && cvr > 0.10) {
      return {
        label: 'Scale Recommended',
        icon: CheckCircle,
        className: 'bg-green-100 text-green-800 border-green-200',
        iconColor: 'text-green-600'
      }
    } else if (conversions >= 3) {
      return {
        label: 'Statistically Significant',
        icon: TrendingUp,
        className: 'bg-blue-100 text-blue-800 border-blue-200',
        iconColor: 'text-blue-600'
      }
    } else if (creative.status === 'testing') {
      return {
        label: 'In Progress',
        icon: Clock,
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        iconColor: 'text-yellow-600'
      }
    } else {
      return {
        label: 'Draft',
        icon: AlertCircle,
        className: 'bg-gray-100 text-gray-800 border-gray-200',
        iconColor: 'text-gray-600'
      }
    }
  }

  const filteredCreatives = creatives.filter(c => {
    if (filter === 'all') return true
    const status = getStatusBadge(c)
    if (filter === 'testing') return status.label === 'In Progress'
    if (filter === 'significant') return status.label === 'Statistically Significant'
    if (filter === 'scale') return status.label === 'Scale Recommended'
    return true
  })

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Creative Lab</h1>
          <p className="mt-2 text-gray-600">
            Manage and analyze your video creatives with AI-powered insights
          </p>
        </div>
        <button
          onClick={() => window.location.href = '/upload'}
          className="btn btn-primary flex items-center gap-2"
        >
          <Upload className="h-5 w-5" />
          Upload New Creative
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'testing', 'significant', 'scale'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              filter === f
                ? 'bg-purple-600 text-white shadow-md'
                : 'bg-white text-gray-700 border border-gray-200 hover:border-purple-300'
            }`}
          >
            {f === 'all' ? 'All' :
             f === 'testing' ? 'In Progress' :
             f === 'significant' ? 'Significant' :
             'Scale Ready'}
          </button>
        ))}
      </div>

      {/* Creatives Grid */}
      {filteredCreatives.length === 0 ? (
        <div className="card py-16 text-center">
          <Video className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No creatives yet</h3>
          <p className="text-gray-600 mb-6">
            Upload your first video creative to start testing
          </p>
          <button
            onClick={() => window.location.href = '/upload'}
            className="btn btn-primary"
          >
            Upload Video
          </button>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCreatives.map((creative) => {
            const status = getStatusBadge(creative)
            const StatusIcon = status.icon
            const cvr = creative.clicks > 0 ? ((creative.conversions / creative.clicks) * 100) : 0

            return (
              <div
                key={creative.id}
                className="card hover:shadow-xl transition-all cursor-pointer group"
              >
                {/* Video Thumbnail */}
                <div className="relative aspect-video bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg mb-4 overflow-hidden">
                  {creative.thumbnail_url ? (
                    <img
                      src={creative.thumbnail_url}
                      alt={creative.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <Video className="h-16 w-16 text-purple-300" />
                    </div>
                  )}

                  {/* Status Badge */}
                  <div className={`absolute top-2 right-2 px-3 py-1 rounded-full border flex items-center gap-1.5 ${status.className}`}>
                    <StatusIcon className={`h-3.5 w-3.5 ${status.iconColor}`} />
                    <span className="text-xs font-medium">{status.label}</span>
                  </div>
                </div>

                {/* Creative Info */}
                <h3 className="font-bold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors">
                  {creative.name}
                </h3>

                {/* AI Tags */}
                <div className="space-y-2 mb-4">
                  {creative.hook_type && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Hook:</span>
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">
                        {creative.hook_type}
                      </span>
                    </div>
                  )}
                  {creative.emotion && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Emotion:</span>
                      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded font-medium">
                        {creative.emotion}
                      </span>
                    </div>
                  )}
                  {creative.target_audience_pain && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Pain:</span>
                      <span className="px-2 py-0.5 bg-pink-100 text-pink-700 rounded font-medium">
                        {creative.target_audience_pain.replace('_', ' ')}
                      </span>
                    </div>
                  )}
                  {creative.pacing && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Pacing:</span>
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                        {creative.pacing}
                      </span>
                    </div>
                  )}
                  {creative.psychotype && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Psychotype:</span>
                      <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded font-medium text-xs">
                        {creative.psychotype}
                      </span>
                    </div>
                  )}
                  {creative.features?.retention_triggers && (
                    <div className="flex items-start justify-between text-sm">
                      <span className="text-gray-600 whitespace-nowrap">Retention:</span>
                      <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded font-medium text-xs text-right">
                        {creative.features.retention_triggers}
                      </span>
                    </div>
                  )}
                  {creative.features?.visual_elements && (
                    <div className="flex items-start justify-between text-sm">
                      <span className="text-gray-600 whitespace-nowrap">Visual:</span>
                      <span className="px-2 py-0.5 bg-cyan-100 text-cyan-700 rounded font-medium text-xs text-right">
                        {creative.features.visual_elements}
                      </span>
                    </div>
                  )}
                  {creative.features?.winning_elements && (
                    <div className="col-span-2 mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                      <span className="font-semibold text-yellow-800">🏆 Winning:</span>
                      <p className="text-yellow-700 mt-1">{creative.features.winning_elements}</p>
                    </div>
                  )}
                </div>

                {/* Timeline (Раскадровка) */}
                {creative.features?.timeline && creative.features.timeline.length > 0 && (
                  <div className="mt-3 p-3 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
                    <h4 className="text-xs font-bold text-purple-900 mb-2 flex items-center gap-1">
                      <span>🎬</span> Timeline
                    </h4>
                    <div className="space-y-2">
                      {creative.features.timeline.map((frame, idx) => (
                        <div key={idx} className="bg-white/70 p-2 rounded border border-purple-100">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-1.5 py-0.5 bg-purple-600 text-white text-xs font-bold rounded">
                              {frame.timestamp}
                            </span>
                            {frame.cta_presence && (
                              <span className="px-1.5 py-0.5 bg-green-500 text-white text-xs rounded">CTA</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-700 mb-1">{frame.what_happens}</p>
                          {frame.retention_hook && (
                            <p className="text-xs text-orange-600">🎯 {frame.retention_hook}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

                {/* Metrics */}
                <div className="grid grid-cols-3 gap-2 pt-4 border-t border-gray-100">
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Clicks</p>
                    <p className="text-lg font-bold text-gray-900">{creative.clicks || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Conv.</p>
                    <p className="text-lg font-bold text-gray-900">{creative.conversions || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">CVR</p>
                    <p className={`text-lg font-bold ${
                      cvr > 10 ? 'text-green-600' :
                      cvr > 5 ? 'text-yellow-600' :
                      'text-gray-900'
                    }`}>
                      {cvr.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <button
                    onClick={() => handleAnalyze(creative.id)}
                    disabled={analyzingId === creative.id}
                    className="flex-1 btn btn-secondary text-sm py-2 flex items-center justify-center gap-1"
                  >
                    {analyzingId === creative.id ? (
                      <>
                        <div className="h-3 w-3 animate-spin rounded-full border-2 border-purple-600 border-t-transparent"></div>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Analyze
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleDelete(creative.id, creative.name)}
                    disabled={deletingId === creative.id}
                    className="btn btn-secondary text-sm py-2 px-3 text-red-600 hover:bg-red-50"
                  >
                    {deletingId === creative.id ? (
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>

                {/* Scale CTA */}
                {status.label === 'Scale Recommended' && (
                  <div className="mt-2">
                    <button className="w-full btn btn-primary text-sm py-2">
                      🚀 Scale to Ads
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default CreativeLab
