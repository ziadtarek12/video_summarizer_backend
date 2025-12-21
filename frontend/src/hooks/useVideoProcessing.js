import { useState, useCallback } from 'react'
import { apiService, pollJob } from '../services/api'
import { v4 as uuidv4 } from 'uuid' // NOTE: I might need to install uuid or just use a simple generator

export function useVideoProcessing() {
    const [status, setStatus] = useState('idle') // idle, uploading, transcribing, processing_features, completed, error
    const [progress, setProgress] = useState(0)
    const [logs, setLogs] = useState([])
    const [results, setResults] = useState(null)
    const [error, setError] = useState(null)

    // Feature configuration
    const [features, setFeatures] = useState({
        transcribe: true,
        summarize: false,
        clips: false,
        chat: false
    })

    const addLog = useCallback((message, type = 'info') => {
        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false })
        setLogs(prev => [...prev, { message, type, timestamp }])
    }, [])

    const reset = () => {
        setStatus('idle')
        setProgress(0)
        setLogs([])
        setResults(null)
        setError(null)
    }

    // Set results directly from library video or update existing results
    // Allows reprocessing without re-transcription and adding features incrementally
    const setResultsFromLibrary = (libraryData) => {
        setResults(prev => {
            const newResults = {
                ...(prev || {}),
                transcript: libraryData.transcript || prev?.transcript,
                videoPath: libraryData.videoPath || prev?.videoPath,
                videoId: libraryData.videoId || prev?.videoId,
                fromLibrary: true
            }
            // Add optional fields if present
            if (libraryData.summary !== undefined) newResults.summary = libraryData.summary
            if (libraryData.chatSessionId !== undefined) newResults.chatSessionId = libraryData.chatSessionId
            if (libraryData.clips !== undefined) newResults.clips = libraryData.clips
            return newResults
        })
        if (!results) {
            addLog(`Loaded video from library (ID: ${libraryData.videoId})`, 'success')
        }
        setStatus('completed')
    }

    const toggleFeature = (featureId) => {
        setFeatures(prev => ({
            ...prev,
            [featureId]: !prev[featureId]
        }))
    }

    const processVideo = async (input, inputType = 'file', settings = {}) => {
        reset()
        setStatus('uploading')
        addLog('Starting video processing pipeline...', 'info')

        try {
            let transcriptionResult

            const commonOptions = {
                language: null, // Auto-detect
                model: 'base', // Whisper model
                device: 'auto'
            }

            // 1. Transcribe (and upload if file)
            if (inputType === 'file') {
                addLog(`Uploading file: ${input.name} (${(input.size / (1024 * 1024)).toFixed(2)} MB)`, 'loading')

                const response = await apiService.transcribeFile(input, commonOptions, (progressEvent) => {
                    setProgress(progressEvent.percent)
                })
                transcriptionResult = response.data
                addLog('Upload completed.', 'success')
            } else {
                addLog(`Processing YouTube URL: ${input}`, 'loading')
                const response = await apiService.transcribeUrl(input, commonOptions)
                transcriptionResult = response.data
            }

            // 2. Poll for Transcription Completion
            setStatus('transcribing')
            addLog(`Job started: ${transcriptionResult.job_id}`, 'info')

            const job = await pollJob(transcriptionResult.job_id, (jobStatus) => {
                if (jobStatus.status === 'processing') {
                    // 
                }
            })

            addLog('Transcription completed successfully.', 'success')

            // Store initial results with full job data
            const currentResults = {
                transcript: job.result.transcript_text, // Updated backend returns plain text here
                jobId: job.id,
                videoPath: job.result.video_path,
                videoId: job.result.video_id  // Video ID for persisting summary/clips
            }

            // 3. Process Optional Features
            setStatus('processing_features')

            if (features.summarize) {
                addLog(`Generating Summary (${settings.outputLanguage})...`, 'loading')
                try {
                    // Pass full settings including model and language
                    const summaryRes = await apiService.summarize(currentResults.transcript, {
                        output_language: settings.outputLanguage,
                        model: settings.model,
                        provider: settings.provider,
                        video_id: currentResults.videoId  // Persist to database
                    })
                    addLog('Summary generated.', 'success')
                    currentResults.summary = summaryRes.data
                } catch (e) {
                    addLog(`Summarization failed: ${e.message}`, 'error')
                }
            }

            setResults(currentResults)
            setStatus('completed')
            addLog('All processing finished.', 'success')

        } catch (err) {
            console.error(err)
            setError(err.message)
            setStatus('error')
            addLog(`Error: ${err.message}`, 'error')
        }
    }

    return {
        status,
        progress,
        logs,
        results,
        error,
        features,
        toggleFeature,
        processVideo,
        reset,
        setResultsFromLibrary
    }
}
