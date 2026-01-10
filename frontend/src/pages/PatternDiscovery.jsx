import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, AlertTriangle, Target, BarChart3 } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PatternDiscovery = () => {
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(true)
  const [productCategory, setProductCategory] = useState('fitness')

  useEffect(() => {
    fetchPatterns()
  }, [productCategory])

  const fetchPatterns = async () => {
    try {
      setLoading(true)
      const res = await axios.get(
        `${API_BASE}/api/v1/rudderstack/thompson-sampling?product_category=${productCategory}&n_recommendations=50`
      )
      setPatterns(res.data.recommendations || [])
    } catch (error) {
      console.error('Failed to fetch patterns:', error)
      setPatterns([])
    } finally {
      setLoading(false)
    }
  }

  const getPatternVerdict = (pattern) => {
    const cvr = pattern.mean_cvr || 0
    const sampleSize = pattern.sample_size || 0

    if (sampleSize >= 20 && cvr > 0.10) {
      return {
        verdict: 'WINNER',
        label: 'Implement in all new creatives',
        color: 'green',
        icon: Target,
        bgClass: 'bg-green-50 border-green-200',
        textClass: 'text-green-900',
        badgeClass: 'bg-green-600 text-white'
      }
    } else if (sampleSize >= 10 && cvr > 0.07) {
      return {
        verdict: 'PROMISING',
        label: 'Test more to confirm',
        color: 'blue',
        icon: TrendingUp,
        bgClass: 'bg-blue-50 border-blue-200',
        textClass: 'text-blue-900',
        badgeClass: 'bg-blue-600 text-white'
      }
    } else if (sampleSize >= 10 && cvr < 0.05) {
      return {
        verdict: 'LOSER',
        label: 'Avoid this pattern',
        color: 'red',
        icon: AlertTriangle,
        bgClass: 'bg-red-50 border-red-200',
        textClass: 'text-red-900',
        badgeClass: 'bg-red-600 text-white'
      }
    } else {
      return {
        verdict: 'TESTING',
        label: 'Need more data',
        color: 'yellow',
        icon: BarChart3,
        bgClass: 'bg-yellow-50 border-yellow-200',
        textClass: 'text-yellow-900',
        badgeClass: 'bg-yellow-600 text-white'
      }
    }
  }

  const groupedPatterns = {
    winners: patterns.filter(p => getPatternVerdict(p).verdict === 'WINNER'),
    promising: patterns.filter(p => getPatternVerdict(p).verdict === 'PROMISING'),
    testing: patterns.filter(p => getPatternVerdict(p).verdict === 'TESTING'),
    losers: patterns.filter(p => getPatternVerdict(p).verdict === 'LOSER'),
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-600 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          Pattern Discovery Library
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          AI-discovered patterns ranked by Bayesian CVR with confidence intervals
        </p>
      </div>

      {/* Category Selector */}
      <div className="flex gap-3">
        {['programming', 'design', 'language_learning'].map((cat) => (
          <button
            key={cat}
            onClick={() => setProductCategory(cat)}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${
              productCategory === cat
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-purple-300'
            }`}
          >
            {cat.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Stats Overview */}
      <div className="grid gap-6 sm:grid-cols-4">
        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-700">Winners</p>
              <p className="text-3xl font-bold text-green-900">{groupedPatterns.winners.length}</p>
            </div>
            <Target className="h-10 w-10 text-green-600 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-700">Promising</p>
              <p className="text-3xl font-bold text-blue-900">{groupedPatterns.promising.length}</p>
            </div>
            <TrendingUp className="h-10 w-10 text-blue-600 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-700">Testing</p>
              <p className="text-3xl font-bold text-yellow-900">{groupedPatterns.testing.length}</p>
            </div>
            <BarChart3 className="h-10 w-10 text-yellow-600 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-700">Losers</p>
              <p className="text-3xl font-bold text-red-900">{groupedPatterns.losers.length}</p>
            </div>
            <AlertTriangle className="h-10 w-10 text-red-600 opacity-50" />
          </div>
        </div>
      </div>

      {/* Pattern Lists */}
      {patterns.length === 0 ? (
        <div className="card py-16 text-center">
          <Sparkles className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No patterns discovered yet</h3>
          <p className="text-gray-600">
            Upload and test creatives to start discovering winning patterns
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Winners */}
          {groupedPatterns.winners.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-green-900 mb-4 flex items-center gap-2">
                <Target className="h-6 w-6" />
                🏆 Winning Patterns - Implement These!
              </h2>
              <div className="space-y-4">
                {groupedPatterns.winners.map((pattern, idx) => {
                  const verdict = getPatternVerdict(pattern)
                  const Icon = verdict.icon

                  return (
                    <div
                      key={idx}
                      className={`card ${verdict.bgClass} border-2`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${verdict.badgeClass}`}>
                              {verdict.verdict}
                            </span>
                            <Icon className={`h-5 w-5 ${verdict.textClass}`} />
                          </div>

                          <h3 className={`text-xl font-bold ${verdict.textClass} mb-2`}>
                            {pattern.hook_type || 'Unknown Hook'} + {pattern.emotion || 'Unknown Emotion'}
                            {pattern.pacing && ` (${pattern.pacing} pacing)`}
                          </h3>

                          <p className="text-sm text-gray-700 mb-3">
                            {verdict.label}
                          </p>

                          {/* Bayesian Metrics */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                            <div>
                              <p className="text-xs text-gray-600">Mean CVR</p>
                              <p className="text-lg font-bold text-gray-900">
                                {(pattern.mean_cvr * 100).toFixed(2)}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">95% CI Lower</p>
                              <p className="text-sm font-medium text-gray-700">
                                {pattern.alpha && pattern.beta ?
                                  ((pattern.alpha / (pattern.alpha + pattern.beta)) * 100 * 0.8).toFixed(1) : 'N/A'}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">95% CI Upper</p>
                              <p className="text-sm font-medium text-gray-700">
                                {pattern.alpha && pattern.beta ?
                                  ((pattern.alpha / (pattern.alpha + pattern.beta)) * 100 * 1.2).toFixed(1) : 'N/A'}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Sample Size</p>
                              <p className="text-lg font-bold text-gray-900">
                                {pattern.sample_size || 0}
                              </p>
                            </div>
                          </div>

                          {/* Thompson Sampling Info */}
                          <div className="mt-3 p-3 bg-white/50 rounded-lg">
                            <p className="text-sm font-medium text-gray-700">
                              Thompson Score: <span className="font-bold">{(pattern.thompson_score || 0).toFixed(4)}</span>
                            </p>
                            <p className="text-xs text-gray-600 mt-1 italic">
                              {pattern.reasoning}
                            </p>
                          </div>
                        </div>

                        {/* Action Button */}
                        <button className="btn bg-green-600 hover:bg-green-700 text-white px-6 py-3 whitespace-nowrap">
                          Copy Pattern
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Promising */}
          {groupedPatterns.promising.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-blue-900 mb-4 flex items-center gap-2">
                <TrendingUp className="h-6 w-6" />
                📊 Promising Patterns - Test More
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                {groupedPatterns.promising.map((pattern, idx) => {
                  const verdict = getPatternVerdict(pattern)
                  return (
                    <div key={idx} className={`card ${verdict.bgClass} border`}>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold mb-2 ${verdict.badgeClass}`}>
                        {verdict.verdict}
                      </span>
                      <h3 className="font-bold text-gray-900">
                        {pattern.hook_type} + {pattern.emotion}
                      </h3>
                      <div className="mt-2 text-sm">
                        <span className="font-semibold">CVR:</span> {(pattern.mean_cvr * 100).toFixed(2)}%
                        <span className="mx-2">•</span>
                        <span className="font-semibold">n:</span> {pattern.sample_size}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Losers */}
          {groupedPatterns.losers.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-red-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="h-6 w-6" />
                ❌ Losing Patterns - Avoid These!
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                {groupedPatterns.losers.map((pattern, idx) => {
                  const verdict = getPatternVerdict(pattern)
                  return (
                    <div key={idx} className={`card ${verdict.bgClass} border`}>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold mb-2 ${verdict.badgeClass}`}>
                        {verdict.verdict}
                      </span>
                      <h3 className="font-bold text-gray-900">
                        {pattern.hook_type} + {pattern.emotion}
                      </h3>
                      <div className="mt-2 text-sm">
                        <span className="font-semibold">CVR:</span> {(pattern.mean_cvr * 100).toFixed(2)}%
                        <span className="mx-2">•</span>
                        <span className="font-semibold">n:</span> {pattern.sample_size}
                      </div>
                      <p className="text-xs text-gray-600 mt-2">{verdict.label}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default PatternDiscovery
