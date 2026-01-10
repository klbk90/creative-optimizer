import { useState, useEffect } from 'react'
import { Zap, TrendingUp, Lightbulb } from 'lucide-react'
import { creativeAPI } from '../services/api'

const Patterns = () => {
  const [topPatterns, setTopPatterns] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [productCategory, setProductCategory] = useState('language_learning')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPatterns()
  }, [productCategory])

  const fetchPatterns = async () => {
    try {
      setLoading(true)

      // Fetch top patterns
      const { data: patterns } = await creativeAPI.getTopPatterns({
        product_category: productCategory,
        limit: 10,
      })
      setTopPatterns(patterns)

      // Fetch Thompson Sampling recommendations
      const { data: recs } = await creativeAPI.getNextPatterns({
        product_category: productCategory,
        n_patterns: 5,
      })
      setRecommendations(recs.recommended_patterns || [])
    } catch (error) {
      console.error('Failed to fetch patterns:', error)
      setTopPatterns([])
      setRecommendations([])
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
        <h1 className="text-3xl font-bold text-gray-900">Pattern Optimization</h1>
        <p className="mt-2 text-gray-600">
          AI-powered pattern recommendations using Thompson Sampling
        </p>
      </div>

      {/* Category Selector */}
      <div className="card">
        <label className="label">Product Category</label>
        <select
          className="input max-w-md"
          value={productCategory}
          onChange={(e) => setProductCategory(e.target.value)}
        >
          <option value="language_learning">Language Learning</option>
          <option value="coding">Coding Education</option>
          <option value="fitness">Fitness & Health</option>
          <option value="finance">Finance</option>
          <option value="productivity">Productivity</option>
          <option value="lootbox">Lootbox/Gaming</option>
        </select>
      </div>

      {/* Thompson Sampling Recommendations */}
      <div className="card">
        <div className="mb-4 flex items-center gap-2">
          <Lightbulb className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-bold text-gray-900">
            Recommended Patterns to Test Next
          </h2>
        </div>
        <p className="mb-4 text-sm text-gray-600">
          Thompson Sampling balances exploitation (proven winners) and exploration (untested patterns)
        </p>

        {recommendations.length === 0 ? (
          <div className="rounded-lg bg-yellow-50 p-4">
            <p className="text-sm text-yellow-800">
              Not enough data for recommendations yet. Upload and test more creatives to train the model.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-gray-200 bg-white p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                        #{idx + 1}
                      </span>
                      <h3 className="font-bold text-gray-900">
                        {rec.hook_type} + {rec.emotion}
                      </h3>
                    </div>
                    <p className="mt-2 text-sm text-gray-600">{rec.reasoning}</p>
                    <div className="mt-3 flex gap-4">
                      <div>
                        <p className="text-xs text-gray-500">Expected CVR</p>
                        <p className="font-medium text-gray-900">
                          {(rec.expected_cvr * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Priority</p>
                        <p className="font-medium text-gray-900">
                          {(rec.priority * 100).toFixed(0)}%
                        </p>
                      </div>
                      {rec.sample_size && (
                        <div>
                          <p className="text-xs text-gray-500">Sample Size</p>
                          <p className="font-medium text-gray-900">
                            {rec.sample_size} tests
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="ml-4">
                    <div
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        rec.priority > 0.7
                          ? 'bg-green-100 text-green-800'
                          : rec.priority > 0.4
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {rec.priority > 0.7 ? 'High Priority' : rec.priority > 0.4 ? 'Medium' : 'Low'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Performing Patterns */}
      <div className="card">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-6 w-6 text-green-500" />
          <h2 className="text-xl font-bold text-gray-900">
            Top Performing Patterns
          </h2>
        </div>

        {topPatterns.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            No pattern data available yet. Start testing creatives to build your pattern library.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr className="text-left text-sm font-medium text-gray-500">
                  <th className="pb-3">Rank</th>
                  <th className="pb-3">Hook Type</th>
                  <th className="pb-3">Emotion</th>
                  <th className="pb-3">Pacing</th>
                  <th className="pb-3">Tests</th>
                  <th className="pb-3">Avg CVR</th>
                  <th className="pb-3">Conversions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {topPatterns.map((pattern, idx) => (
                  <tr key={pattern.id} className="text-sm">
                    <td className="py-3">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-xs font-bold text-gray-700">
                        {idx + 1}
                      </span>
                    </td>
                    <td className="py-3 font-medium text-gray-900">
                      {pattern.hook_type}
                    </td>
                    <td className="py-3 text-gray-600">{pattern.emotion}</td>
                    <td className="py-3 text-gray-600">{pattern.pacing}</td>
                    <td className="py-3 text-gray-600">{pattern.sample_size}</td>
                    <td className="py-3">
                      <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                        {(pattern.avg_cvr * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 font-medium text-gray-900">
                      {pattern.total_conversions || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model Info */}
      <div className="card bg-blue-50">
        <div className="flex items-start gap-3">
          <Zap className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="font-bold text-blue-900">Thompson Sampling</h3>
            <p className="mt-1 text-sm text-blue-700">
              This AI algorithm learns which creative patterns work best for your product.
              It balances testing proven winners (exploitation) with exploring new patterns (exploration).
              The more you test, the smarter the recommendations become.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Patterns
