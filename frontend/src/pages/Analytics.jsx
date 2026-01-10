import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { creativeAPI } from '../services/api'

const Analytics = () => {
  const [patternStats, setPatternStats] = useState([])
  const [trendData, setTrendData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)

      // Fetch creatives data
      const { data: creatives } = await creativeAPI.getCreatives({ limit: 100 })

      // Group by patterns
      const patternMap = {}
      creatives.forEach((creative) => {
        const pattern = `${creative.hook_type}_${creative.emotion}`
        if (!patternMap[pattern]) {
          patternMap[pattern] = {
            pattern,
            hook: creative.hook_type,
            emotion: creative.emotion,
            count: 0,
            totalCVR: 0,
            conversions: 0,
          }
        }
        patternMap[pattern].count++
        patternMap[pattern].totalCVR += creative.conversion_rate || 0
        patternMap[pattern].conversions += creative.conversions || 0
      })

      const patterns = Object.values(patternMap).map((p) => ({
        ...p,
        avgCVR: (p.totalCVR / p.count) * 100,
      })).sort((a, b) => b.avgCVR - a.avgCVR)

      setPatternStats(patterns)

      // Create trend data (by date)
      const dateMap = {}
      creatives.forEach((creative) => {
        if (!creative.created_at) return
        const date = new Date(creative.created_at).toLocaleDateString()
        if (!dateMap[date]) {
          dateMap[date] = {
            date,
            creatives: 0,
            avgCVR: 0,
            totalCVR: 0,
          }
        }
        dateMap[date].creatives++
        dateMap[date].totalCVR += (creative.conversion_rate || 0) * 100
      })

      const trends = Object.values(dateMap)
        .map((d) => ({
          ...d,
          avgCVR: d.totalCVR / d.creatives,
        }))
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(-14) // Last 14 days

      setTrendData(trends)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
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
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-2 text-gray-600">
          Deep dive into your creative performance data
        </p>
      </div>

      {/* CVR by Pattern */}
      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          CVR by Pattern (Hook + Emotion)
        </h2>
        {patternStats.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No data available yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={patternStats} margin={{ bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="pattern"
                angle={0}
                height={80}
                interval={0}
                tick={{ fontSize: 11 }}
              />
              <YAxis label={{ value: 'CVR (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="avgCVR" fill="#0ea5e9" name="Average CVR %" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* CVR Trend Over Time */}
      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          CVR Trend Over Time
        </h2>
        {trendData.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No trend data available yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis label={{ value: 'CVR (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="avgCVR"
                stroke="#0ea5e9"
                strokeWidth={2}
                name="Average CVR %"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Pattern Performance Table */}
      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          Pattern Performance Details
        </h2>
        {patternStats.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No patterns found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr className="text-left text-sm font-medium text-gray-500">
                  <th className="pb-3">Hook Type</th>
                  <th className="pb-3">Emotion</th>
                  <th className="pb-3">Creatives</th>
                  <th className="pb-3">Avg CVR</th>
                  <th className="pb-3">Total Conversions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {patternStats.map((stat, idx) => (
                  <tr key={idx} className="text-sm">
                    <td className="py-3 font-medium text-gray-900">
                      {stat.hook}
                    </td>
                    <td className="py-3 text-gray-600">{stat.emotion}</td>
                    <td className="py-3 text-gray-600">{stat.count}</td>
                    <td className="py-3">
                      <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
                        {stat.avgCVR.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 font-medium text-gray-900">
                      {stat.conversions}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics
