const API_BASE = '';

export class VideoSummarizerAPI {

    static async transcribe(url) {
        const response = await fetch(`${API_BASE}/api/transcribe/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!response.ok) throw new Error('Transcription request failed');
        return await response.json();
    }

    static async transcribeFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/transcribe/file`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('File transcription request failed');
        return await response.json();
    }

    static async getJobStatus(jobId) {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to get job status');
        return await response.json();
    }

    static async summarize({ transcript_text, transcript_path }) {
        const response = await fetch(`${API_BASE}/api/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transcript_text,
                transcript_path,
                provider: 'google' // Default
            })
        });
        if (!response.ok) throw new Error('Summarization request failed');
        return await response.json();
    }

    static async extractClips(videoPath, transcriptPath) {
        const response = await fetch(`${API_BASE}/api/extract-clips`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_path: videoPath,
                transcript_path: transcriptPath,
                num_clips: 3,
                merge: true
            })
        });
        if (!response.ok) throw new Error('Clip extraction request failed');
        return await response.json();
    }

    static async startChat({ transcript_text, transcript_path }) {
        const response = await fetch(`${API_BASE}/api/chat/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transcript_text,
                transcript_path
            })
        });
        if (!response.ok) throw new Error('Failed to start chat session');
        return await response.json();
    }

    static async sendChatMessage(sessionId, message, onChunk) {
        const response = await fetch(`${API_BASE}/api/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message })
        });

        if (!response.ok) throw new Error('Failed to send message');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            onChunk(chunk);
        }
    }

    // Helper to poll until completion
    static async pollJob(jobId, interval = 2000) {
        return new Promise((resolve, reject) => {
            const check = async () => {
                try {
                    const status = await this.getJobStatus(jobId);
                    if (status.status === 'completed') {
                        resolve(status);
                    } else if (status.status === 'failed') {
                        reject(status.error || 'Job failed');
                    } else {
                        setTimeout(check, interval);
                    }
                } catch (e) {
                    reject(e);
                }
            };
            check();
        });
    }
}
