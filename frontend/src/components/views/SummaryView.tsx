
import { useState, useEffect } from 'react'
import Markdown from 'react-markdown'
import { Loader2, Sparkles, RefreshCcw } from 'lucide-react'
import { summarize, getJobStatus } from '../../services/api'
import { cn } from '../../lib/utils'

interface SummaryViewProps {
    files: any // Contains paths to transcript
}

export function SummaryView({ files }: SummaryViewProps) {
    const [loading, setLoading] = useState(false)
    const [summary, setSummary] = useState<{ text: string, key_points: string[] } | null>(null)
    const [jobId, setJobId] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    // Polling for summary job
    useEffect(() => {
        if (!jobId) return

        const interval = setInterval(async () => {
            try {
                const data = await getJobStatus(jobId)
                if (data.status === 'completed') {
                    setSummary(data.result)
                    setLoading(false)
                    setJobId(null)
                } else if (data.status === 'failed') {
                    setError(data.error || "Summarization failed")
                    setLoading(false)
                    setJobId(null)
                }
            } catch (err) {
                console.error(err)
            }
        }, 2000)

        return () => clearInterval(interval)
    }, [jobId])

    const handleGenerate = async (lang: 'english' | 'original') => {
        setLoading(true)
        setError(null)
        try {
            // We need transcript text. If backend supports path, we send path.
            // My backend `summarize_endpoint` supports `transcript_path`.
            // `files.transcript` is the .srt path. `files.text` is the .txt path.
            // Let's use `files.text` if available, else transcript.
            const path = files.text || files.transcript

            const { job_id } = await summarize("", "google", lang)
            // Wait, I need to pass path. My API service `summarize` takes text.
            // I need to update API service to take path OR text.
            // Or I fetch text here and send it.
            // I'll update API service call in next step or sending text.
            // Since I can't restart API service easily, let's just fetch text here and send it.

            let textToSend = ""
            if (path) {
                const res = await fetch(`/${path}`)
                textToSend = await res.text()
            }

            const { job_id: jid } = await summarize(textToSend, "google", lang)
            setJobId(jid)
        } catch (e: any) {
            setError(e.message)
            setLoading(false)
        }
    }

    if (loading || jobId) {
        return (
            <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                <Sparkles className="text-primary mb-4 animate-spin-slow" size={48} />
                <p className="text-lg font-medium">Generating AI Summary...</p>
                <p className="text-muted text-sm">Analyzing key points and context</p>
            </div>
        )
    }

    if (summary) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="prose prose-invert max-w-none">
                    <h3 className="text-xl font-bold text-primary mb-4">Overview</h3>
                    <Markdown>{summary.text}</Markdown>
                </div>

                <div className="bg-surface/50 rounded-xl p-6 border border-white/5">
                    <h3 className="text-xl font-bold text-primary mb-4">Key Points</h3>
                    <ul className="space-y-3">
                        {summary.key_points?.map((point, i) => (
                            <li key={i} className="flex gap-3 text-sm md:text-base">
                                <span className="bg-primary/20 text-primary w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5">
                                    {i + 1}
                                </span>
                                <span>{point}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="flex justify-end">
                    <button onClick={() => setSummary(null)} className="flex items-center gap-2 text-sm text-muted hover:text-white transition-colors">
                        <RefreshCcw size={14} /> Regenerate
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-2">
                <Sparkles size={32} className="text-primary" />
            </div>
            <div>
                <h3 className="text-xl font-bold">Generate Summary</h3>
                <p className="text-muted max-w-sm mx-auto mt-2">
                    Use AI to extract key insights, summary, and action items from the transcript.
                </p>
            </div>

            {error && <p className="text-red-400 bg-red-400/10 px-4 py-2 rounded-lg">{error}</p>}

            <div className="flex gap-4">
                <button
                    onClick={() => handleGenerate('original')}
                    className="px-6 py-3 rounded-xl bg-surface hover:bg-white/10 border border-white/10 transition-all font-medium"
                >
                    Original Language
                </button>
                <button
                    onClick={() => handleGenerate('english')}
                    className="px-6 py-3 rounded-xl bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/25 transition-all font-medium"
                >
                    English Summary
                </button>
            </div>
        </div>
    )
}
