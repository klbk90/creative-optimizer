import { useState, useEffect } from 'react'
import { Video, TrendingUp, DollarSign, Zap, Sparkles, Users, Target } from 'lucide-react'
import StatCard from '../components/StatCard'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const DashboardPro = () => {
  const [stats, setStats] = useState({
    totalCreatives: 0,
    totalSpend: 0,
    totalRevenue: 0,
    globalCVR: 0,
    estimatedSavings: 0,
    activeTests: 0,
  })
  const [topInfluencers, setTopInfluencers] = useState([])
  const [patternTrends, setPatternTrends] = useState({ winning: 0, losing: 0, testing: 0 })
  const [topPatterns, setTopPatterns] = useState([])
  const [loading, setLoading] = useState(false) // Changed to false to debug
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      console.log('Fetching dashboard data...')

      // Fetch all data in parallel
      const [creativesRes, patternsRes, influencersRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/creative/list`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/api/v1/rudderstack/thompson-sampling?product_category=fitness&n_recommendations=10`).catch(() => ({ data: { recommendations: [] } })),
        fetchTopInfluencers(),
      ])

      const creatives = Array.isArray(creativesRes.data) ? creativesRes.data : []
      const patterns = patternsRes.data.recommendations || []

      // Calculate metrics
      const totalCreatives = creatives.length
      const activeTests = creatives.filter(c => c.status === 'testing').length

      const totalSpend = creatives.reduce((sum, c) => {
        const spend = (c.production_cost || 0) + (c.media_spend || 0)
        return sum + spend
      }, 0) / 100 // cents to dollars

      const totalRevenue = creatives.reduce((sum, c) => sum + (c.revenue || 0), 0) / 100

      const totalConversions = creatives.reduce((sum, c) => sum + (c.conversions || 0), 0)
      const totalImpressions = creatives.reduce((sum, c) => sum + (c.impressions || 0), 0)
      const globalCVR = totalImpressions > 0 ? (totalConversions / totalImpressions) * 100 : 0

      // Estimated Savings calculation
      // Сколько бы потратили на A/B тест всех креативов vs сколько потратили на micro-influencer тесты
      const traditionalTestCost = totalCreatives * 1000 // $1000 per creative for traditional A/B test
      const actualSpend = totalSpend
      const estimatedSavings = Math.max(0, traditionalTestCost - actualSpend)

      setStats({
        totalCreatives,
        totalSpend: totalSpend.toFixed(2),
        totalRevenue: totalRevenue.toFixed(2),
        globalCVR: globalCVR.toFixed(2),
        estimatedSavings: estimatedSavings.toFixed(2),
        activeTests,
      })

      // Pattern trends
      const winning = patterns.filter(p => (p.sample_size || 0) > 10 && (p.mean_cvr || 0) > 0.10).length
      const losing = patterns.filter(p => (p.sample_size || 0) > 10 && (p.mean_cvr || 0) < 0.05).length
      const testing = patterns.filter(p => (p.sample_size || 0) <= 10).length

      setPatternTrends({ winning, losing, testing })
      setTopPatterns(patterns.slice(0, 5))

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setError(error.message)
    } finally {
      setLoading(false)
      console.log('Dashboard loaded')
    }
  }

  const fetchTopInfluencers = async () => {
    try {
      // TODO: Replace with real influencer endpoint when available
      // For now return empty array
      return { data: [] }
    } catch (error) {
      console.error('Failed to fetch influencers:', error)
      return { data: [] }
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-purple-600 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => { setError(null); fetchDashboardData(); }}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          Creative Optimizer Dashboard
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          AI-powered creative testing &amp; pattern discovery for EdTech
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Spend"
          value={`$${stats.totalSpend}`}
          icon={DollarSign}
          subtitle="On micro-influencer tests"
          trend={{ value: '-60%', isPositive: true, label: 'vs traditional A/B' }}
        />
        <StatCard
          title="Total Revenue"
          value={`$${stats.totalRevenue}`}
          icon={TrendingUp}
          subtitle="From tested creatives"
          trend={{ value: `${stats.globalCVR}%`, label: 'CVR' }}
        />
        <StatCard
          title="Estimated Savings"
          value={`$${stats.estimatedSavings}`}
          icon={Sparkles}
          subtitle="vs traditional testing"
          highlight={true}
        />
        <StatCard
          title="Active Tests"
          value={stats.activeTests}
          icon={Zap}
          subtitle={`of ${stats.totalCreatives} total creatives`}
        />
      </div>

      {/* Pattern Discovery Status */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-700">Winning Patterns</p>
              <p className="mt-1 text-3xl font-bold text-green-900">{patternTrends.winning}</p>
            </div>
            <Target className="h-12 w-12 text-green-600 opacity-50" />
          </div>
          <p className="mt-2 text-xs text-green-700">CVR &gt; 10%, sample &gt; 10</p>
        </div>

        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-700">Testing Patterns</p>
              <p className="mt-1 text-3xl font-bold text-yellow-900">{patternTrends.testing}</p>
            </div>
            <Zap className="h-12 w-12 text-yellow-600 opacity-50" />
          </div>
          <p className="mt-2 text-xs text-yellow-700">Need more data (sample &lt; 10)</p>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-700">Losing Patterns</p>
              <p className="mt-1 text-3xl font-bold text-red-900">{patternTrends.losing}</p>
            </div>
            <Video className="h-12 w-12 text-red-600 opacity-50" />
          </div>
          <p className="mt-2 text-xs text-red-700">CVR &lt; 5%, avoid these</p>
        </div>
      </div>

      {/* Top Patterns */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">🎯 Top Performing Patterns</h2>
          <button
            onClick={() => window.location.href = '/patterns'}
            className="text-purple-600 hover:text-purple-700 font-medium text-sm"
          >
            View All →
          </button>
        </div>

        {topPatterns.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            <Sparkles className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p>No patterns discovered yet. Upload creatives to start testing!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {topPatterns.map((pattern, idx) => (
              <div
                key={idx}
                className="p-4 rounded-lg border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '🎯'}
                      </span>
                      <div>
                        <p className="font-semibold text-gray-900">
                          {pattern.hook_type || 'Unknown'} + {pattern.emotion || 'Unknown'}
                        </p>
                        <p className="text-sm text-gray-600">
                          Sample: {pattern.sample_size || 0} • Thompson Score: {(pattern.thompson_score || 0).toFixed(3)}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-purple-600">
                      {((pattern.mean_cvr || 0) * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">CVR</p>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-600 italic">
                  {pattern.reasoning || 'No insights yet'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Influencers */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            <Users className="inline h-6 w-6 mr-2 text-purple-600" />
            Top Influencers by ROI
          </h2>
          <button
            onClick={() => window.location.href = '/influencers'}
            className="text-purple-600 hover:text-purple-700 font-medium text-sm"
          >
            Manage Influencers →
          </button>
        </div>

        {topInfluencers.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            <Users className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p>No influencer data yet. Start a campaign to track performance!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr className="text-left text-sm font-semibold text-gray-700">
                  <th className="pb-3 pl-4">Influencer</th>
                  <th className="pb-3">Followers</th>
                  <th className="pb-3">Clicks</th>
                  <th className="pb-3">Conversions</th>
                  <th className="pb-3">CVR</th>
                  <th className="pb-3">Revenue</th>
                  <th className="pb-3 pr-4">ROI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {topInfluencers.map((inf, idx) => (
                  <tr key={idx} className="text-sm hover:bg-purple-50 transition-colors">
                    <td className="py-4 pl-4">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold">
                          {inf.handle[0]?.toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900">@{inf.handle}</span>
                      </div>
                    </td>
                    <td className="py-4 text-gray-600">{inf.followers.toLocaleString()}</td>
                    <td className="py-4 text-gray-600">{inf.clicks}</td>
                    <td className="py-4 text-gray-900 font-medium">{inf.conversions}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        parseFloat(inf.cvr) > 10 ? 'bg-green-100 text-green-800' :
                        parseFloat(inf.cvr) > 5 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {inf.cvr}%
                      </span>
                    </td>
                    <td className="py-4 font-medium text-gray-900">${inf.revenue.toFixed(2)}</td>
                    <td className="py-4 pr-4">
                      <span className={`text-lg font-bold ${
                        parseFloat(inf.roi) > 2 ? 'text-green-600' :
                        parseFloat(inf.roi) > 1 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {inf.roi}x
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 sm:grid-cols-3">
        <button
          onClick={() => window.location.href = '/upload'}
          className="card hover:shadow-xl transition-all hover:scale-105 cursor-pointer bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200"
        >
          <Video className="h-10 w-10 text-purple-600 mb-3" />
          <h3 className="text-lg font-bold text-gray-900">Upload Creative</h3>
          <p className="mt-2 text-sm text-gray-600">
            Test new video with AI analysis
          </p>
        </button>

        <button
          onClick={() => window.location.href = '/patterns'}
          className="card hover:shadow-xl transition-all hover:scale-105 cursor-pointer bg-gradient-to-br from-green-50 to-green-100 border-green-200"
        >
          <Sparkles className="h-10 w-10 text-green-600 mb-3" />
          <h3 className="text-lg font-bold text-gray-900">Pattern Library</h3>
          <p className="mt-2 text-sm text-gray-600">
            View all discovered patterns
          </p>
        </button>

        <button
          onClick={() => window.location.href = '/influencers'}
          className="card hover:shadow-xl transition-all hover:scale-105 cursor-pointer bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200"
        >
          <Users className="h-10 w-10 text-pink-600 mb-3" />
          <h3 className="text-lg font-bold text-gray-900">Find Influencers</h3>
          <p className="mt-2 text-sm text-gray-600">
            Search micro-influencers via Modash
          </p>
        </button>
      </div>
    </div>
  )
}

export default DashboardPro
