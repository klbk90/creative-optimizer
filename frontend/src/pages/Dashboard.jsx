import { useState, useEffect } from 'react'
import { Video, TrendingUp, DollarSign, Zap } from 'lucide-react'
import StatCard from '../components/StatCard'
import { creativeAPI } from '../services/api'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCreatives: 0,
    avgCVR: 0,
    totalRevenue: 0,
    activeTests: 0,
  })
  const [topCreatives, setTopCreatives] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const { data } = await creativeAPI.getCreatives({ limit: 100 })

      // Calculate stats
      const totalCreatives = data.length
      const activeTests = data.filter(c => !c.test_completed).length
      const avgCVR = data.reduce((sum, c) => sum + (c.conversion_rate || 0), 0) / totalCreatives || 0
      const totalRevenue = data.reduce((sum, c) => sum + (c.revenue_cents || 0), 0) / 100

      setStats({
        totalCreatives,
        avgCVR: (avgCVR * 100).toFixed(2),
        totalRevenue: totalRevenue.toFixed(2),
        activeTests,
      })

      // Get top 5 performers
      const sorted = [...data]
        .filter(c => c.conversion_rate > 0)
        .sort((a, b) => (b.conversion_rate || 0) - (a.conversion_rate || 0))
        .slice(0, 5)

      setTopCreatives(sorted)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your creative performance
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Creatives"
          value={stats.totalCreatives}
          icon={Video}
          subtitle="All time"
        />
        <StatCard
          title="Average CVR"
          value={`${stats.avgCVR}%`}
          icon={TrendingUp}
          subtitle="Conversion rate"
        />
        <StatCard
          title="Total Revenue"
          value={`$${stats.totalRevenue}`}
          icon={DollarSign}
          subtitle="All creatives"
        />
        <StatCard
          title="Active Tests"
          value={stats.activeTests}
          icon={Zap}
          subtitle="Currently running"
        />
      </div>

      {/* Top Performers */}
      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          Top Performing Creatives
        </h2>

        {topCreatives.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No creatives with conversions yet. Upload and test your first creative!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr className="text-left text-sm font-medium text-gray-500">
                  <th className="pb-3">Creative Name</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">CVR</th>
                  <th className="pb-3">Impressions</th>
                  <th className="pb-3">Conversions</th>
                  <th className="pb-3">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {topCreatives.map((creative) => (
                  <tr key={creative.id} className="text-sm">
                    <td className="py-3 font-medium text-gray-900">
                      {creative.name}
                    </td>
                    <td className="py-3 text-gray-600">
                      {creative.creative_type}
                    </td>
                    <td className="py-3">
                      <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                        {((creative.conversion_rate || 0) * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">
                      {(creative.impressions || 0).toLocaleString()}
                    </td>
                    <td className="py-3 text-gray-600">
                      {creative.conversions || 0}
                    </td>
                    <td className="py-3 font-medium text-gray-900">
                      ${((creative.revenue_cents || 0) / 100).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 sm:grid-cols-2">
        <div className="card hover:shadow-lg transition-shadow cursor-pointer">
          <h3 className="text-lg font-bold text-gray-900">Upload New Creative</h3>
          <p className="mt-2 text-sm text-gray-600">
            Upload a video and get AI-powered performance predictions
          </p>
          <button
            onClick={() => window.location.href = '/upload'}
            className="btn btn-primary mt-4"
          >
            Upload Video
          </button>
        </div>

        <div className="card hover:shadow-lg transition-shadow cursor-pointer">
          <h3 className="text-lg font-bold text-gray-900">Pattern Recommendations</h3>
          <p className="mt-2 text-sm text-gray-600">
            Get Thompson Sampling recommendations for next tests
          </p>
          <button
            onClick={() => window.location.href = '/patterns'}
            className="btn btn-primary mt-4"
          >
            View Patterns
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
