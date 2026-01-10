import { useState } from 'react'
import { Upload as UploadIcon, Loader2, CheckCircle } from 'lucide-react'
import { creativeAPI } from '../services/api'

const Upload = () => {
  const [file, setFile] = useState(null)
  const [formData, setFormData] = useState({
    creative_name: '',
    product_category: 'language_learning',
    creative_type: 'ugc',
    source_platform: 'tiktok',
  })
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      if (!formData.creative_name) {
        setFormData(prev => ({
          ...prev,
          creative_name: selectedFile.name.replace(/\.[^/.]+$/, '')
        }))
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a video file')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const formDataToSend = new FormData()
      formDataToSend.append('video', file)
      formDataToSend.append('creative_name', formData.creative_name)
      formDataToSend.append('product_category', formData.product_category)
      formDataToSend.append('creative_type', formData.creative_type)
      formDataToSend.append('source_platform', formData.source_platform)
      formDataToSend.append('auto_analyze', 'true')

      const { data } = await creativeAPI.uploadVideo(formDataToSend)
      setResult(data)

      // Reset form
      setFile(null)
      setFormData({
        creative_name: '',
        product_category: 'language_learning',
        creative_type: 'ugc',
        source_platform: 'tiktok',
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Creative</h1>
        <p className="mt-2 text-gray-600">
          Upload a video and get AI-powered performance predictions
        </p>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* File Upload */}
        <div>
          <label className="label">Video File</label>
          <div className="mt-1">
            <label
              htmlFor="file-upload"
              className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 px-6 py-10 hover:bg-gray-100"
            >
              {file ? (
                <div className="text-center">
                  <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                  <p className="mt-2 text-sm font-medium text-gray-900">
                    {file.name}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div className="text-center">
                  <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm font-medium text-gray-900">
                    Click to upload video
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    MP4, MOV up to 100MB
                  </p>
                </div>
              )}
              <input
                id="file-upload"
                name="file-upload"
                type="file"
                className="sr-only"
                accept="video/*"
                onChange={handleFileChange}
                disabled={uploading}
              />
            </label>
          </div>
        </div>

        {/* Creative Name */}
        <div>
          <label className="label">Creative Name</label>
          <input
            type="text"
            className="input"
            value={formData.creative_name}
            onChange={(e) =>
              setFormData({ ...formData, creative_name: e.target.value })
            }
            required
            disabled={uploading}
          />
        </div>

        {/* Product Category */}
        <div>
          <label className="label">Product Category</label>
          <select
            className="input"
            value={formData.product_category}
            onChange={(e) =>
              setFormData({ ...formData, product_category: e.target.value })
            }
            disabled={uploading}
          >
            <option value="language_learning">Language Learning</option>
            <option value="coding">Coding Education</option>
            <option value="fitness">Fitness & Health</option>
            <option value="finance">Finance</option>
            <option value="productivity">Productivity</option>
            <option value="lootbox">Lootbox/Gaming</option>
          </select>
        </div>

        {/* Creative Type */}
        <div>
          <label className="label">Creative Type</label>
          <select
            className="input"
            value={formData.creative_type}
            onChange={(e) =>
              setFormData({ ...formData, creative_type: e.target.value })
            }
            disabled={uploading}
          >
            <option value="ugc">UGC (User Generated)</option>
            <option value="micro_influencer">Micro Influencer</option>
            <option value="studio">Studio</option>
            <option value="spark_ad">Spark Ad</option>
          </select>
        </div>

        {/* Source Platform */}
        <div>
          <label className="label">Source Platform</label>
          <select
            className="input"
            value={formData.source_platform}
            onChange={(e) =>
              setFormData({ ...formData, source_platform: e.target.value })
            }
            disabled={uploading}
          >
            <option value="tiktok">TikTok</option>
            <option value="facebook">Facebook/Instagram</option>
            <option value="youtube">YouTube</option>
            <option value="google">Google Ads</option>
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="btn btn-primary w-full"
          disabled={uploading || !file}
        >
          {uploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <UploadIcon className="mr-2 h-4 w-4" />
              Upload & Analyze
            </>
          )}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card space-y-4 bg-green-50">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <h3 className="text-lg font-bold text-green-900">
              Analysis Complete!
            </h3>
          </div>

          {result.analysis && (
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Predicted CVR
                </p>
                <p className="text-2xl font-bold text-green-900">
                  {(result.analysis.predicted_cvr * 100).toFixed(2)}%
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-700">Hook Type</p>
                  <p className="text-gray-900">{result.analysis.hook_type}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Emotion</p>
                  <p className="text-gray-900">{result.analysis.emotion}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Pacing</p>
                  <p className="text-gray-900">{result.analysis.pacing}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    Confidence
                  </p>
                  <p className="text-gray-900">
                    {(result.analysis.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {result.analysis.reasoning && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Analysis</p>
                  <p className="text-sm text-gray-600">
                    {result.analysis.reasoning}
                  </p>
                </div>
              )}
            </div>
          )}

          <button
            onClick={() => window.location.href = '/creatives'}
            className="btn btn-primary"
          >
            View All Creatives
          </button>
        </div>
      )}
    </div>
  )
}

export default Upload
