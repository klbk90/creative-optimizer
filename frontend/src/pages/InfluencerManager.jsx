import { useState, useEffect } from 'react'
import { Search, Users, Link as LinkIcon, TrendingUp, ExternalLink, Sparkles, Plus, CheckCircle } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const InfluencerManager = () => {
  const [activeTab, setActiveTab] = useState('campaigns') // campaigns, search
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState(null)

  // Search state
  const [searchParams, setSearchParams] = useState({
    niche: 'fitness',
    min_followers: 10000,
    max_followers: 50000,
    min_engagement_rate: 2.5,
    platform: 'instagram',
    limit: 20
  })
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [addingToTest, setAddingToTest] = useState({})

  useEffect(() => {
    if (activeTab === 'campaigns') {
      fetchCampaigns()
    }
  }, [activeTab])

  const fetchCampaigns = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/creative/list`)
      const creatives = Array.isArray(res.data) ? res.data : []
      setCampaigns(creatives)
      if (creatives.length > 0 && !selectedCampaign) {
        setSelectedCampaign(creatives[0])
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    }
  }

  const handleFindMatch = async () => {
    try {
      setSearching(true)
      const creativeId = selectedCampaign?.id || null

      const res = await axios.post(
        `${API_BASE}/api/v1/influencers/search${creativeId ? `?creative_id=${creativeId}` : ''}`,
        searchParams
      )

      setSearchResults(res.data || [])
      setActiveTab('search')
    } catch (error) {
      console.error('Search failed:', error)
      alert('Search failed. Check console for details.')
    } finally {
      setSearching(false)
    }
  }

  const handleAddToTest = async (influencer) => {
    if (!selectedCampaign) {
      alert('Please select a campaign first')
      return
    }

    try {
      setAddingToTest(prev => ({ ...prev, [influencer.id]: true }))

      const res = await axios.post(`${API_BASE}/api/v1/influencers/add-to-test`, {
        creative_id: selectedCampaign.id,
        influencer_handle: influencer.handle,
        influencer_followers: influencer.followers,
        platform: influencer.platform
      })

      alert(`✅ ${res.data.message}\n\n📋 Landing URL:\n${res.data.landing_url}\n\nCopy this link and send it to ${influencer.handle}`)

    } catch (error) {
      console.error('Failed to add to test:', error)
      alert('Failed to add influencer to test')
    } finally {
      setAddingToTest(prev => ({ ...prev, [influencer.id]: false }))
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getScoreBadge = (score) => {
    if (score >= 80) return 'Excellent Match'
    if (score >= 60) return 'Good Match'
    return 'Weak Match'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Influencer Manager</h1>
          <p className="mt-1 text-sm text-gray-500">
            Find micro-influencers and test creatives with AI-powered matching
          </p>
        </div>

        {selectedCampaign && (
          <div className="text-right">
            <p className="text-sm text-gray-500">Selected Campaign</p>
            <p className="font-medium text-gray-900">{selectedCampaign.name}</p>
            <p className="text-xs text-gray-400">{selectedCampaign.product_category}</p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('campaigns')}
            className={`${
              activeTab === 'campaigns'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
            } whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium`}
          >
            <Users className="mr-2 inline h-5 w-5" />
            Campaigns
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`${
              activeTab === 'search'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
            } whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium`}
          >
            <Search className="mr-2 inline h-5 w-5" />
            Find Match ({searchResults.length})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'campaigns' && (
        <div className="space-y-6">
          {/* Campaign Selector */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold">Select Campaign to Test</h3>
            <div className="space-y-2">
              {campaigns.map((campaign) => (
                <button
                  key={campaign.id}
                  onClick={() => setSelectedCampaign(campaign)}
                  className={`${
                    selectedCampaign?.id === campaign.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } flex w-full items-center justify-between rounded-lg border-2 p-4 text-left transition`}
                >
                  <div>
                    <p className="font-medium text-gray-900">{campaign.name}</p>
                    <p className="text-sm text-gray-500">
                      {campaign.hook_type} • {campaign.emotion} • {campaign.product_category}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">CVR: {(campaign.cvr * 100).toFixed(1)}%</p>
                    <p className="text-xs text-gray-500">{campaign.conversions} conversions</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Search Parameters */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold">Search Parameters</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Niche</label>
                <input
                  type="text"
                  value={searchParams.niche}
                  onChange={(e) => setSearchParams({ ...searchParams, niche: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Platform</label>
                <select
                  value={searchParams.platform}
                  onChange={(e) => setSearchParams({ ...searchParams, platform: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                >
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Min Followers</label>
                <input
                  type="number"
                  value={searchParams.min_followers}
                  onChange={(e) => setSearchParams({ ...searchParams, min_followers: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Followers</label>
                <input
                  type="number"
                  value={searchParams.max_followers}
                  onChange={(e) => setSearchParams({ ...searchParams, max_followers: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Min Engagement Rate (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={searchParams.min_engagement_rate}
                  onChange={(e) => setSearchParams({ ...searchParams, min_engagement_rate: parseFloat(e.target.value) })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Limit</label>
                <input
                  type="number"
                  value={searchParams.limit}
                  onChange={(e) => setSearchParams({ ...searchParams, limit: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500"
                />
              </div>
            </div>

            <button
              onClick={handleFindMatch}
              disabled={searching || !selectedCampaign}
              className="mt-6 w-full rounded-lg bg-primary-600 px-4 py-3 font-semibold text-white hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {searching ? 'Searching...' : '🔍 Find Match'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'search' && (
        <div className="space-y-4">
          {searchResults.length === 0 ? (
            <div className="card text-center py-12">
              <Search className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-gray-500">No influencers found. Try adjusting search parameters.</p>
              <button
                onClick={() => setActiveTab('campaigns')}
                className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
              >
                ← Back to Campaigns
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Found {searchResults.length} influencers • Sorted by AI Score
                </p>
                <button
                  onClick={() => setActiveTab('campaigns')}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  ← Back to Campaigns
                </button>
              </div>

              {searchResults.map((influencer) => (
                <div key={influencer.id} className="card hover:shadow-md transition">
                  <div className="flex items-start justify-between">
                    {/* Influencer Info */}
                    <div className="flex items-start space-x-4 flex-1">
                      {influencer.avatar_url && (
                        <img
                          src={influencer.avatar_url}
                          alt={influencer.handle}
                          className="h-16 w-16 rounded-full"
                        />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-lg font-semibold text-gray-900">{influencer.handle}</h3>
                          <span className="text-sm text-gray-500">{influencer.name}</span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{influencer.bio}</p>

                        {/* Stats */}
                        <div className="mt-2 flex items-center space-x-4 text-sm">
                          <span className="text-gray-500">
                            <Users className="inline h-4 w-4 mr-1" />
                            {(influencer.followers / 1000).toFixed(1)}K
                          </span>
                          <span className="text-gray-500">
                            <TrendingUp className="inline h-4 w-4 mr-1" />
                            {influencer.engagement_rate.toFixed(1)}% ER
                          </span>
                          <span className="text-gray-500">
                            {influencer.platform}
                          </span>
                        </div>

                        {/* Niches */}
                        <div className="mt-2 flex flex-wrap gap-1">
                          {influencer.niche.map((n, i) => (
                            <span key={i} className="inline-block rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                              {n}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* AI Score */}
                    <div className="ml-4 text-right">
                      <div className={`inline-flex items-center rounded-lg px-3 py-2 font-bold ${getScoreColor(influencer.ai_score)}`}>
                        <Sparkles className="mr-2 h-5 w-5" />
                        <span className="text-2xl">{influencer.ai_score.toFixed(0)}</span>
                      </div>
                      <p className="mt-1 text-xs font-medium text-gray-600">{getScoreBadge(influencer.ai_score)}</p>
                      <p className="mt-2 text-xs text-gray-500 max-w-xs">{influencer.ai_reasoning}</p>

                      {/* Add to Test Button */}
                      <button
                        onClick={() => handleAddToTest(influencer)}
                        disabled={addingToTest[influencer.id]}
                        className="mt-3 w-full rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700 disabled:bg-gray-300"
                      >
                        {addingToTest[influencer.id] ? (
                          'Adding...'
                        ) : (
                          <>
                            <Plus className="inline h-4 w-4 mr-1" />
                            Add to Test
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default InfluencerManager
