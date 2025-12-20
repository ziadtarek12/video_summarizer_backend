import axios from 'axios'

const API = axios.create({
    baseURL: '/api'
})

export const apiService = {
    // Transcribe URL
    transcribeUrl: async (url, options) => {
        // options: { device, model, language }
        return API.post('/transcribe/url', null, {
            params: { url, ...options }
        })
    },

    // Transcribe File with upload progress
    transcribeFile: async (file, options, onProgress) => {
        const formData = new FormData()
        formData.append('file', file)

        // Add other options to query params if needed or strictly follow backend
        return API.post('/transcribe/file', formData, {
            params: options,
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                if (onProgress) {
                    onProgress({
                        percent: percentCompleted,
                        loaded: progressEvent.loaded,
                        total: progressEvent.total
                    })
                }
            }
        })
    },

    getJobStatus: async (jobId) => {
        return API.get(`/jobs/${jobId}`)
    },

    summarize: async (transcriptText, options) => {
        // options: { provider, model, output_language }
        // Backend expects 'transcript' text in body
        return API.post('/summarize', {
            transcript_text: transcriptText,
        }, { params: options })
    },

    extractClips: async (transcriptSrt, videoPath, options) => {
        // options: { num_clips, provider, model }
        return API.post('/extract-clips', {
            transcript: transcriptSrt,
            video_path: videoPath
        }, { params: options })
    },

    startChat: async (transcript) => {
        return API.post('/chat/start', { transcript })
    },

    sendChatMessage: async (sessionId, message) => {
        return API.post(`/chat/${sessionId}/message`, { message }, {
            responseType: 'stream' // Note: Handling streams in axios is tricky, fetch might be better for this specifically
        })
    }
}

// Helper to poll job status
export const pollJob = async (jobId, onStatus, interval = 2000) => {
    return new Promise((resolve, reject) => {
        const check = async () => {
            try {
                const response = await apiService.getJobStatus(jobId)
                const job = response.data

                onStatus(job)

                if (job.status === 'completed') {
                    resolve(job)
                } else if (job.status === 'failed') {
                    reject(new Error(job.error || 'Job failed'))
                } else {
                    setTimeout(check, interval)
                }
            } catch (error) {
                reject(error)
            }
        }
        check()
    })
}
