/**
 * API Handlers
 */

import axios from 'axios'
import { Media } from '../types'

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000/'

// Create axios instance with better configuration
const api = axios.create({
  baseURL: BACKEND_URL,
  timeout: 30000, // 30 second timeout for regular operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create axios instance with longer timeout for delete operations
const deleteApi = axios.create({
  baseURL: BACKEND_URL,
  timeout: 60000, // 60 second timeout for delete operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  },
)

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => {
    console.log('Response interceptor - response received:', response)
    console.log('Response status:', response.status)
    console.log('Response data:', response.data)
    return response
  },
  (error) => {
    console.log('Response interceptor - error received:', error)
    if (error.response) {
      // Server responded with error status
      console.error('API Response Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // Request was made but no response received
      console.error('API No Response Error:', error.request)
    } else {
      // Something else happened
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  },
)

const INFO_URL = `server/info`
const DELETED_SIZES = `server/deleted-sizes`
const DUPES_URL = `content/dupes`
const SAMPLES_URL = `content/samples`
const DELETE_MEDIA_URL = `delete/media`
const IGNORE_MEDIA_URL = `content/ignore`
const UNIGNORE_MEDIA_URL = `content/unignore`

export const getServerInfo = (): Promise<any> => {
  return api.get(INFO_URL)
}

export const getDeletedSizes = (): Promise<any> => {
  return api.get(DELETED_SIZES)
}

export const getDupeContent = (): Promise<any> => {
  console.log('getDupeContent called - making API request...')
  const startTime = Date.now()

  console.log('About to make fetch call...')
  
  // Create AbortController for timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout
  
  return fetch(`${BACKEND_URL}${DUPES_URL}`, { signal: controller.signal })
    .then((response) => {
      clearTimeout(timeoutId)
      console.log('Fetch response received:', response)
      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Check response size
      const contentLength = response.headers.get('content-length')
      if (contentLength) {
        console.log('Response size:', contentLength, 'bytes')
      }

      return response.text() // Get as text first to check size
    })
    .then((text) => {
      console.log('Response text received, length:', text.length, 'characters')

      if (text.length > 1000000) {
        // 1MB limit
        console.warn('Response is very large, may cause performance issues')
      }

      try {
        const data = JSON.parse(text)
        console.log('JSON parsed successfully, data keys:', Object.keys(data))
        console.log('Data array length:', data.data?.length || 0)

        const duration = Date.now() - startTime
        console.log(`getDupeContent completed in ${duration}ms`)
        return { data, status: 200 }
      } catch (parseError) {
        console.error('JSON parse error:', parseError)
        console.error('Response preview:', text.substring(0, 500))
        const errorMessage = parseError instanceof Error ? parseError.message : String(parseError)
        throw new Error(`Failed to parse JSON: ${errorMessage}`)
      }
    })
    .catch((error) => {
      clearTimeout(timeoutId)
      if (error.name === 'AbortError') {
        console.error('Request timed out after 60 seconds')
        throw new Error('Request timed out after 60 seconds')
      }
      console.error('Fetch error:', error)
      throw error
    })
}

export const getSampleContent = (): Promise<any> => {
  return api.get(SAMPLES_URL)
}

export const ignoreMedia = (contentKey: string): Promise<any> => {
  return api.post(IGNORE_MEDIA_URL, {
    content_key: contentKey,
  })
}

export const unIgnoreMedia = (contentKey: string): Promise<any> => {
  return api.post(UNIGNORE_MEDIA_URL, {
    content_key: contentKey,
  })
}

export const deleteMedia = (library: string, contentKey: string, mediaId: number): Promise<any> => {
  return deleteApi.post(DELETE_MEDIA_URL, {
    library_name: library,
    content_key: contentKey,
    media_id: mediaId,
  })
}

export const deleteMediaBatch = async (
  items: Array<{ library: string; contentKey: string; media: Media }>,
  batchSize: number = 10
): Promise<{ success: number; failed: number; errors: Array<{ mediaId: number; error: string }> }> => {
  const results = {
    success: 0,
    failed: 0,
    errors: [] as Array<{ mediaId: number; error: string }>
  }

  // Process items in batches
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize)
    console.log(`Processing delete batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(items.length / batchSize)} with ${batch.length} items`)
    
    try {
      // Process batch concurrently with Promise.all
      const batchPromises = batch.map(item => 
        deleteApi.post(DELETE_MEDIA_URL, {
          library_name: item.library,
          content_key: item.contentKey,
          media_id: item.media.id,
        }).then(() => ({ success: true, mediaId: item.media.id, error: null }))
        .catch((error) => ({ 
          success: false, 
          mediaId: item.media.id, 
          error: error.response?.data?.error || error.message || 'Delete operation failed'
        }))
      )
      
      const batchResults = await Promise.all(batchPromises)
      
      // Count results
      batchResults.forEach(result => {
        if (result.success) {
          results.success++
        } else {
          results.failed++
          if (result.error) {
            results.errors.push({ mediaId: result.mediaId, error: result.error })
          }
        }
      })
      
      console.log(`Batch completed: ${batchResults.filter(r => r.success).length}/${batch.length} successful`)
      
      // Small delay between batches to avoid overwhelming the server
      if (i + batchSize < items.length) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // 1 second delay between batches
      }
      
    } catch (error: any) {
      console.error(`Batch ${Math.floor(i / batchSize) + 1} failed:`, error)
      // Mark all items in this batch as failed
      batch.forEach(item => {
        results.failed++
        results.errors.push({ 
          mediaId: item.media.id, 
          error: error?.response?.data?.error || error?.message || 'Batch processing failed'
        })
      })
    }
  }
  
  console.log(`Batch delete completed: ${results.success} successful, ${results.failed} failed`)
  return results
}
