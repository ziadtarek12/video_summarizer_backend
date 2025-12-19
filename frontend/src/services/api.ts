
import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Vite proxy handles this
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface JobStatus {
    id: string;
    type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    result?: any;
    error?: string;
    files?: Record<string, string>;
    updated_at: string;
}

export const transcribeUrl = async (url: string, language?: string, model?: string) => {
    const response = await api.post('/transcribe/url', { url, language, model });
    return response.data; // { job_id: string }
};

export const transcribeFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/transcribe/file', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data; // { job_id: string }
};

export const getJobStatus = async (jobId: string) => {
    const response = await api.get<JobStatus>(`/jobs/${jobId}`);
    return response.data;
};

export const summarize = async (transcriptText: string, provider: string, outputLanguage: string) => {
    const response = await api.post('/summarize', {
        transcript_text: transcriptText,
        provider,
        output_language: outputLanguage
    });
    return response.data; // { job_id: string }
};

export const startChat = async (transcriptText: string, provider: string) => {
    const response = await api.post('/chat/start', {
        transcript_text: transcriptText,
        provider
    });
    return response.data; // { session_id: string }
};

export const extractClips = async (videoPath: string, transcriptPath: string, numClips: number) => {
    // Note: In real app, we need to pass the paths that the backend knows about
    // Ideally, the previous job result contained these paths.
    const response = await api.post('/extract-clips', {
        video_path: videoPath,
        transcript_path: transcriptPath,
        num_clips: numClips
    });
    return response.data;
}

// Helper for streaming chat is handled in component via fetch/EventSource usually, 
// but since we did a simple stream endpoint, we can use fetch + ReadableStream.
