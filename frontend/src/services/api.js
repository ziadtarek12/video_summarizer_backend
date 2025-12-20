import axios from 'axios'

const API = axios.create({
    baseURL: '/api'
})

// Request interceptor to add token
API.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const apiService = {
    // Auth
    login: async (email, password) => {
        const formData = new FormData();
        formData.append('username', email); // OAuth2 expects 'username'
        formData.append('password', password);
        return API.post('/auth/token', formData);
    },
    register: async (email, password) => {
        return API.post('/auth/register', { email, password });
    },
    getMe: async () => {
        return API.get('/auth/me');
    },
    getLibrary: async () => {
        return API.get('/library');
    },

    // Transcribe URL
    transcribeUrl: async (url, options) => {
        // options: { device, model, language }
        return API.post('/transcribe/url', { url, ...options });
    },

    // Transcribe File with upload progress
    transcribeFile: async (file, options, onProgress) => {
        const formData = new FormData()
        formData.append('file', file)

        // Append options to formData
        if (options.language) formData.append('language', options.language);
        if (options.model) formData.append('model', options.model);
        if (options.device) formData.append('device', options.device);

        return API.post('/transcribe/file', formData, {
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
        return API.post('/summarize', {
            transcript_text: transcriptText,
            ...options
        })
    },

    extractClips: async (transcriptPath, videoPath, options) => {
        // options: { num_clips, provider, model }
        return API.post('/extract-clips', {
            transcript_path: transcriptPath,
            video_path: videoPath,
            ...options
        })
    },

    startChat: async (transcriptText) => {
        return API.post('/chat/start', { transcript_text: transcriptText })
    },

    sendChatMessage: async (sessionId, message) => {
        return API.post('/chat/message', {
            session_id: sessionId,
            message: message
        }, {
            responseType: 'stream'
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
