
import { useState, useRef } from 'react'
import { Upload, Youtube, ArrowRight, Loader2, Link } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../lib/utils'
import { transcribeUrl, transcribeFile } from '../services/api'

interface VideoInputProps {
    onJobCreated: (jobId: string) => void
}

export function VideoInput({ onJobCreated }: VideoInputProps) {
    const [activeTab, setActiveTab] = useState<'url' | 'file'>('url')
    const [url, setUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleSubmitUrl = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!url) return

        setLoading(true)
        try {
            const { job_id } = await transcribeUrl(url)
            onJobCreated(job_id)
        } catch (error) {
            console.error(error)
            alert("Failed to start transcription")
        } finally {
            setLoading(false)
        }
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setLoading(true)
        try {
            const { job_id } = await transcribeFile(file)
            onJobCreated(job_id)
        } catch (error) {
            console.error(error)
            alert("Failed to upload file")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] gap-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center space-y-4"
            >
                <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
                    Transform Video into <span className="text-primary">Insight</span>
                </h2>
                <p className="text-muted text-lg max-w-2xl">
                    AI-powered transcription, summarization, and chat for your videos using Gemini 1.5 Pro.
                </p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="w-full max-w-lg"
            >
                <div className="bg-surface rounded-2xl p-2 flex mb-6 border border-white/5">
                    <button
                        onClick={() => setActiveTab('url')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all font-medium text-sm",
                            activeTab === 'url' ? "bg-primary text-white shadow-lg shadow-primary/25" : "text-muted hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Youtube size={18} />
                        YouTube URL
                    </button>
                    <button
                        onClick={() => setActiveTab('file')}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all font-medium text-sm",
                            activeTab === 'file' ? "bg-primary text-white shadow-lg shadow-primary/25" : "text-muted hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Upload size={18} />
                        Upload File
                    </button>
                </div>

                <div className="bg-surface/50 border border-white/5 rounded-3xl p-8 backdrop-blur-sm shadow-2xl">
                    {activeTab === 'url' ? (
                        <form onSubmit={handleSubmitUrl} className="space-y-4">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-muted group-focus-within:text-primary transition-colors">
                                    <Link size={20} />
                                </div>
                                <input
                                    type="url"
                                    placeholder="https://youtube.com/watch?v=..."
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    className="w-full bg-background border border-white/10 rounded-xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-muted/50"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:pointer-events-none"
                            >
                                {loading ? <Loader2 className="animate-spin" /> : <>Start Processing <ArrowRight size={20} /></>}
                            </button>
                        </form>
                    ) : (
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            className="border-2 border-dashed border-white/10 rounded-2xl p-12 flex flex-col items-center justify-center text-center cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all group"
                        >
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                className="hidden"
                                accept="video/*,audio/*"
                            />
                            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform text-primary">
                                <Upload size={32} />
                            </div>
                            <p className="text-lg font-medium group-hover:text-primary transition-colors">Click to upload video</p>
                            <p className="text-sm text-muted mt-2">MP4, MOV, MP3 (Max 2GB)</p>
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    )
}
