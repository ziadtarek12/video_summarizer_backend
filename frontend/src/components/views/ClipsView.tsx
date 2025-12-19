
import { useState, useEffect } from 'react'
import { Scissors, Play, Download, Loader2, AlertCircle } from 'lucide-react'
import { extractClips, getJobStatus } from '../../services/api'
import { cn } from '../../lib/utils'

interface ClipsViewProps {
    files: any
}

export function ClipsView({ files }: ClipsViewProps) {
    const [loading, setLoading] = useState(false)
    const [jobId, setJobId] = useState<string | null>(null)
    const [result, setResult] = useState<{ clips_dir: string, clips_count: number, merged_video?: string } | null>(null)
    const [clips, setClips] = useState<any[]>([])

    // Poll for clips job
    useEffect(() => {
        if (!jobId) return

        const interval = setInterval(async () => {
            try {
                const data = await getJobStatus(jobId)
                if (data.status === 'completed') {
                    setResult(data.result)
                    // Load metadata to get clip details
                    if (data.result.clips_metadata) {
                        try {
                            const res = await fetch(`/${data.result.clips_metadata}`)
                            const json = await res.json()
                            setClips(json)
                        } catch (e) { console.error("Failed to load clips json", e) }
                    }
                    setLoading(false)
                    setJobId(null)
                } else if (data.status === 'failed') {
                    alert("Clip extraction failed: " + data.error)
                    setLoading(false)
                    setJobId(null)
                }
            } catch (err) {
                console.error(err)
            }
        }, 2000)

        return () => clearInterval(interval)
    }, [jobId])

    const handleExtract = async () => {
        setLoading(true)
        try {
            // files.video might be full path on server.
            // files.transcript is srt path
            const { job_id } = await extractClips(files.video, files.transcript, 5)
            setJobId(job_id)
        } catch (e) {
            console.error(e)
            setLoading(false)
            alert("Failed to start clip extraction")
        }
    }

    if (loading || jobId) {
        return (
            <div className="flex flex-col items-center justify-center py-20 animate-pulse text-center">
                <Scissors className="text-primary mb-4 animate-bounce" size={48} />
                <p className="text-lg font-medium">Analyzing & Extracting Clips...</p>
                <p className="text-muted text-sm">Finding the most viral moments</p>
            </div>
        )
    }

    if (result) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {clips.map((clip, i) => (
                        <div key={i} className="bg-surface rounded-xl overflow-hidden border border-white/5 group">
                            <div className="aspect-video bg-black/50 relative flex items-center justify-center">
                                {/* In real app, serve video clip file. 
                                  Path logic: `output/job_id/clips/clip_N.mp4` 
                                  We need to know the relative path. 
                                  The backend returns absolute paths mostly.
                                  We assume `files` are accessible via static mount if they are in output dir.
                                  
                                  files keys: video, transcript, text, etc.
                                  The clip path construction here is tricky without backend providing public URL.
                                  We passed `output_dir` as string.
                               */}
                                <span className="text-muted text-xs">Video Preview Placeholder</span>
                                <Play className="absolute text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-lg" size={48} />
                            </div>
                            <div className="p-4">
                                <h4 className="font-bold mb-1 truncate" title={clip.title}>{clip.title}</h4>
                                <p className="text-sm text-muted mb-4">{clip.rationale}</p>
                                <div className="flex justify-between items-center text-xs text-muted">
                                    <span>{clip.start}s - {clip.end}s</span>
                                    <button className="flex items-center gap-1 hover:text-primary transition-colors">
                                        <Download size={14} /> Download
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-2">
                <Scissors size={32} className="text-primary" />
            </div>
            <div>
                <h3 className="text-xl font-bold">Extract Shorts/Clips</h3>
                <p className="text-muted max-w-sm mx-auto mt-2">
                    Automatically identify and extract the most engaging moments for social media.
                </p>
            </div>

            <button
                onClick={handleExtract}
                className="px-8 py-4 rounded-xl bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/25 transition-all font-bold flex items-center gap-2"
            >
                <Scissors size={20} /> Extract 5 Clips
            </button>
        </div>
    )
}
