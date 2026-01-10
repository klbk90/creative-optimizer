import { useState, useEffect } from 'react'
import { Video, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'
import { creativeAPI } from '../services/api'

const Creatives = () => {
  const [creatives, setCreatives] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, winners, losers, testing

  useEffect(() => {
    fetchCreatives()
  }, [])

  const fetchCreatives = async () => {
    try {
      setLoading(true)
      const { data } = await creativeAPI.getCreatives({ limit: 100 })
      setCreatives(data)
    } catch (error) {
      console.error('Failed to fetch creatives:', error)
    } finally {
      setLoading(false)
    }
  }

  const getFilteredCreatives = () => {
    switch (filter) {
      case 'winners':
        return creatives.filter(c => (c.conversion_rate || 0) > 0.08) // 8%+ CVR
      case 'losers':
        return creatives.filter(c => c.conversions > 0 && (c.conversion_rate || 0) < 0.05) // <5% CVR
      case 'testing':
        return creatives.filter(c => !c.test_completed)
      default:
        return creatives
    }
  }

  const filteredCreatives = getFilteredCreatives()

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Creatives</h1>
          <p className="mt-2 text-gray-600">
            Manage and track your creative performance
          </p>
        </div>
        <button
          onClick={fetchCreatives}
          className="btn btn-secondary flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'winners', 'losers', 'testing'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`btn ${
              filter === f ? 'btn-primary' : 'btn-secondary'
            } capitalize`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Creatives List */}
      {filteredCreatives.length === 0 ? (
        <div className="card py-12 text-center">
          <Video className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600">
            No creatives found. Upload your first creative to get started!
          </p>
          <button
            onClick={() => window.location.href = '/upload'}
            className="btn btn-primary mt-4"
          >
            Upload Creative
          </button>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr className="text-left text-sm font-medium text-gray-500">
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Type</th>
                  <th className="px-6 py-3">Category</th>
                  <th className="px-6 py-3">Predicted CVR</th>
                  <th className="px-6 py-3">Actual CVR</th>
                  <th className="px-6 py-3">Performance</th>
                  <th className="px-6 py-3">Impressions</th>
                  <th className="px-6 py-3">Conversions</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredCreatives.map((creative) => {
                  const predictedCVR = creative.predicted_cvr || 0
                  const actualCVR = creative.conversion_rate || 0
                  const performance = actualCVR > 0 ? ((actualCVR - predictedCVR) / predictedCVR) * 100 : null

                  return (
                    <tr key={creative.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">
                          {creative.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {creative.hook_type} • {creative.emotion}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {creative.creative_type}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {creative.product_category}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium text-gray-900">
                          {(predictedCVR * 100).toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {actualCVR > 0 ? (
                          <span className="text-sm font-medium text-gray-900">
                            {(actualCVR * 100).toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {performance !== null ? (
                          <div className="flex items-center gap-1">
                            {performance > 0 ? (
                              <TrendingUp className="h-4 w-4 text-green-600" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-600" />
                            )}
                            <span
                              className={`text-sm font-medium ${
                                performance > 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {performance > 0 ? '+' : ''}
                              {performance.toFixed(0)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {(creative.impressions || 0).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {creative.conversions || 0}
                      </td>
                      <td className="px-6 py-4">
                        {creative.test_completed ? (
                          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800">
                            Completed
                          </span>
                        ) : (
                          <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
                            Testing
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default Creatives
