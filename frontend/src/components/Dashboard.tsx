
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Loader2, FileText, MessageSquare, Film, CheckCircle2, AlertCircle } from 'lucide-react'
import { getJobStatus, JobStatus } from '../services/api'
import { cn } from '../lib/utils'
import { SummaryView } from './views/SummaryView'
import { ChatView } from './views/ChatView'
import { ClipsView } from './views/ClipsView'

interface DashboardProps {
    jobId: string
    onBack: () => void
}

export function Dashboard({ jobId, onBack }: DashboardProps) {
    const [status, setStatus] = useState<JobStatus | null>(null)
    const [activeTab, setActiveTab] = useState('transcript')

    // Polling for status
    useEffect(() => {
        const poll = async () => {
            try {
                const data = await getJobStatus(jobId)
                setStatus(data)
                if (data.status === 'completed' || data.status === 'failed') {
                    return true // stop polling
                }
            } catch (err) {
                console.error("Polling error", err)
            }
            return false
        }

        const interval = setInterval(async () => {
            const stop = await poll()
            if (stop) clearInterval(interval)
        }, 2000)

        poll() // Initial call

        return () => clearInterval(interval)
    }, [jobId])

    if (!status) {
        return <div className="flex justify-center p-20"><Loader2 className="animate-spin text-primary" size={40} /></div>
    }

    if (status.status === 'failed') {
        return (
            <div className="text-center p-20">
                <div className="w-16 h-16 rounded-full bg-red-500/20 text-red-500 flex items-center justify-center mx-auto mb-4">
                    <AlertCircle size={32} />
                </div>
                <h3 className="text-2xl font-bold mb-2">Processing Failed</h3>
                <p className="text-muted mb-6">{status.error}</p>
                <button onClick={onBack} className="text-primary hover:underline">Try Again</button>
            </div>
        )
    }

    if (status.status === 'pending' || status.status === 'processing') {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <div className="relative mb-8">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
                    <Loader2 size={64} className="text-primary animate-spin relative z-10" />
                </div>
                <h2 className="text-3xl font-bold mb-2">Processing Video...</h2>
                <p className="text-muted max-w-md animate-pulse">
                    Transcribing audio and generating insights. This might take a few minutes depending on the video length.
                </p>
            </div>
        )
    }

    // --- Completed View ---

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <CheckCircle2 className="text-green-500" />
                        Ready
                    </h2>
                    <p className="text-muted text-sm">Processed successfully</p>
                </div>
                <button onClick={onBack} className="text-sm text-muted hover:text-white transition-colors">
                    Start New
                </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-surface mb-8">
                {[
                    { id: 'transcript', label: 'Transcript', icon: FileText },
                    { id: 'summary', label: 'Summary', icon: FileText }, // Different icon maybe?
                    { id: 'chat', label: 'Chat', icon: MessageSquare },
                    { id: 'clips', label: 'Clips', icon: Film },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-3 border-b-2 transition-all font-medium",
                            activeTab === tab.id
                                ? "border-primary text-primary"
                                : "border-transparent text-muted hover:text-white"
                        )}
                    >
                        <tab.icon size={18} />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="bg-surface/30 rounded-2xl p-6 min-h-[500px]">
                {activeTab === 'transcript' && (
                    <TranscriptView files={status.files} />
                )}
                {activeTab === 'summary' && (
                    <SummaryView files={status.files} />
                )}
                {activeTab === 'chat' && (
                    <ChatView files={status.files} />
                )}
                {activeTab === 'clips' && (
                    <ClipsView files={status.files} />
                )}
            </div>
        </div>
    )
}

function TranscriptView({ files }: { files: any }) {
    // In real app, we would fetch the text content.
    // For now, let's just show a placeholder or basic fetch logic
    const [text, setText] = useState("Loading...")

    useEffect(() => {
        if (files?.text) {
            // Since we don't have a direct URL to the file served via API unless we set up static serving...
            // Wait, I did set up `app.mount("/output", ...)` in main.py!
            // So I can fetch it.
            // files.text is the ABSOLUTE path on server.
            // Wait, serving static files usually requires relative path to the static dir?
            // static dir is "output". file path is "output/job_id/transcript.txt".
            // URL would be "/output/job_id/transcript.txt".
            // But file path is absolute or relative?
            // In backend: `output_dir = Path(f"output/{job_id}")`. then `job.files["text"] = str(text_path)` which is "output/job_id/transcript.txt".
            // So it corresponds!

            fetch(`/${files.text}`)
                .then(r => r.text())
                .then(setText)
                .catch(e => setText("Failed to load transcript: " + e.message))
        }
    }, [files])

    return (
        <div className="prose prose-invert max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-300 leading-relaxed">
                {text}
            </pre>
        </div>
    )
}

