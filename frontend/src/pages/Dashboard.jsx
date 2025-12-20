import { useState, useEffect } from 'react'
import { Video, LogOut, Settings, History, Play, RefreshCw, X, Sparkles, MessageSquare, Scissors } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useVideoProcessing } from '../hooks/useVideoProcessing'
import { LogTerminal } from '../components/LogTerminal'
import { FeatureToggles } from '../components/FeatureToggles'
import { UploadSection } from '../components/UploadSection'
import { ResultsDashboard } from '../components/ResultsDashboard'
import { apiService } from '../services/api'
import clsx from 'clsx'
import { motion, AnimatePresence } from 'framer-motion'

export function Dashboard() {
    const { logout, user } = useAuth()
    const {
        status,
        progress,
        logs,
        features,
        toggleFeature,
        processVideo,
        results,
        reset,
        setResultsFromLibrary
    } = useVideoProcessing()

    const [showLibrary, setShowLibrary] = useState(false)
    const [libraryVideos, setLibraryVideos] = useState([])
    const [selectedVideo, setSelectedVideo] = useState(null)
    const [loadingVideo, setLoadingVideo] = useState(false)

    // App configuration from backend
    const [appConfig, setAppConfig] = useState({
        languages: { ar: 'Arabic', en: 'English' },
        models: ['gemini-1.5-flash'],
        default_language: 'ar',
        default_model: 'gemini-1.5-flash'
    })

    const [settings, setSettings] = useState({
        transcriptionLanguage: 'ar',
        outputLanguage: 'english',
        mergeClips: true,
        model: 'gemini-1.5-flash',
    })

    // Fetch app config on mount
    useEffect(() => {
        loadConfig()
    }, [])

    useEffect(() => {
        if (showLibrary) {
            loadLibrary()
        }
    }, [showLibrary])

    const loadConfig = async () => {
        try {
            const res = await apiService.getConfig()
            setAppConfig(res.data)
            // Set defaults from config
            setSettings(prev => ({
                ...prev,
                transcriptionLanguage: res.data.default_language || 'ar',
                model: res.data.default_model || 'gemini-1.5-flash'
            }))
        } catch (e) {
            console.error("Failed to load config", e)
        }
    }

    const loadLibrary = async () => {
        try {
            const res = await apiService.getLibrary()
            setLibraryVideos(res.data)
        } catch (e) {
            console.error("Failed to load library", e)
        }
    }

    const handleSelectLibraryVideo = async (video) => {
        setLoadingVideo(true)
        try {
            const res = await apiService.getVideoDetails(video.id)
            setSelectedVideo(res.data)

            // If video has transcript, allow direct processing without re-transcription
            if (res.data.transcript_text) {
                // Set results from library so user can summarize/chat directly
                if (setResultsFromLibrary) {
                    setResultsFromLibrary({
                        transcript: res.data.transcript_text,
                        videoPath: res.data.file_path,
                        videoId: res.data.id,
                        fromLibrary: true
                    })
                }
            }
            setShowLibrary(false)
        } catch (e) {
            console.error("Failed to load video details", e)
        } finally {
            setLoadingVideo(false)
        }
    }

    const isProcessing = status !== 'idle' && status !== 'completed' && status !== 'error'

    const handleProcess = (input, type) => {
        processVideo(input, type, settings)
    }

    const handleClearSelection = () => {
        setSelectedVideo(null)
        reset()
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white flex">

            {/* Sidebar (Library) */}
            <AnimatePresence>
                {showLibrary && (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 360, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="bg-slate-900/80 backdrop-blur-xl border-r border-slate-800/50 flex flex-col overflow-hidden"
                    >
                        <div className="p-5 border-b border-slate-800/50 flex justify-between items-center bg-gradient-to-r from-primary-500/5 to-transparent">
                            <h2 className="font-bold text-lg bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">Your Library</h2>
                            <button onClick={() => setShowLibrary(false)} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all">
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {libraryVideos.map(vid => (
                                <motion.div
                                    key={vid.id}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => handleSelectLibraryVideo(vid)}
                                    className={clsx(
                                        "p-4 rounded-xl border transition-all cursor-pointer group",
                                        "bg-gradient-to-br from-slate-800/50 to-slate-800/30",
                                        "border-slate-700/50 hover:border-primary-500/50",
                                        "hover:shadow-lg hover:shadow-primary-500/10"
                                    )}
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className="p-2 bg-primary-500/10 rounded-lg group-hover:bg-primary-500/20 transition-colors">
                                            <Play className="w-4 h-4 text-primary-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-medium truncate text-white">{vid.title || vid.filename}</div>
                                            <div className="text-xs text-slate-500 mt-1">{new Date(vid.created_at).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                            {libraryVideos.length === 0 && (
                                <div className="text-center text-slate-500 mt-10 py-8">
                                    <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                    <p>No videos yet. Upload one to get started!</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Header */}
                <header className="flex items-center justify-between px-8 py-4 border-b border-slate-800/50 bg-slate-950/50 backdrop-blur-xl z-10">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => setShowLibrary(!showLibrary)}
                            className={clsx(
                                "p-2.5 rounded-xl transition-all",
                                showLibrary
                                    ? "bg-primary-500/20 text-primary-400"
                                    : "hover:bg-slate-800 text-slate-400 hover:text-white"
                            )}
                            title="Video Library"
                        >
                            <History className="w-5 h-5" />
                        </button>
                        <div className="flex items-center space-x-3">
                            <div className="p-2.5 bg-gradient-to-br from-primary-500/20 to-indigo-500/20 rounded-xl border border-primary-500/20">
                                <Video className="w-6 h-6 text-primary-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                                    Video Summarizer AI
                                </h1>
                                <p className="text-xs text-slate-500">Powered by Whisper & LLM</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                            <span className="text-xs text-slate-500">Logged in as</span>
                            <span className="text-sm text-white font-medium ml-2">{user?.email}</span>
                        </div>
                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 transition-all border border-rose-500/20"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="text-sm font-medium">Sign Out</span>
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-6 md:p-8">
                    <div className="max-w-7xl mx-auto space-y-8">

                        {/* Selected Video from Library Banner */}
                        {selectedVideo && !results && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-gradient-to-r from-primary-500/10 to-indigo-500/10 border border-primary-500/20 rounded-2xl p-4 flex items-center justify-between"
                            >
                                <div className="flex items-center space-x-4">
                                    <div className="p-3 bg-primary-500/20 rounded-xl">
                                        <Video className="w-5 h-5 text-primary-400" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-400">Selected from library</p>
                                        <p className="font-medium text-white">{selectedVideo.title || selectedVideo.filename}</p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-3">
                                    {selectedVideo.transcript_text && (
                                        <span className="text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/20">
                                            ✓ Transcript Ready
                                        </span>
                                    )}
                                    <button
                                        onClick={handleClearSelection}
                                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {/* Action Buttons for Library Video */}
                        {selectedVideo && selectedVideo.transcript_text && !results && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="glass-card p-6"
                            >
                                <h3 className="text-lg font-semibold text-white mb-4">Process This Video</h3>
                                <p className="text-sm text-slate-400 mb-6">
                                    This video already has a transcript. Choose what you'd like to do:
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <button
                                        onClick={async () => {
                                            toggleFeature('summarize')
                                            // Trigger summarization
                                            const res = await apiService.summarize(selectedVideo.transcript_text, {
                                                output_language: settings.outputLanguage,
                                                model: settings.model,
                                                provider: settings.model.includes('gemini') ? 'google' : 'openrouter'
                                            })
                                            setResultsFromLibrary({
                                                transcript: selectedVideo.transcript_text,
                                                videoPath: selectedVideo.file_path,
                                                videoId: selectedVideo.id,
                                                summary: res.data
                                            })
                                        }}
                                        disabled={isProcessing}
                                        className="flex flex-col items-center space-y-3 p-6 bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-xl hover:from-amber-500/20 hover:to-orange-500/20 transition-all disabled:opacity-50"
                                    >
                                        <Sparkles className="w-8 h-8 text-amber-400" />
                                        <div className="text-center">
                                            <div className="font-semibold text-white">Summarize</div>
                                            <div className="text-xs text-slate-400 mt-1">Generate AI summary</div>
                                        </div>
                                    </button>

                                    <button
                                        onClick={async () => {
                                            toggleFeature('chat')
                                            const res = await apiService.startChat(selectedVideo.transcript_text)
                                            setResultsFromLibrary({
                                                transcript: selectedVideo.transcript_text,
                                                videoPath: selectedVideo.file_path,
                                                videoId: selectedVideo.id,
                                                chatSessionId: res.data.session_id
                                            })
                                        }}
                                        disabled={isProcessing}
                                        className="flex flex-col items-center space-y-3 p-6 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl hover:from-indigo-500/20 hover:to-purple-500/20 transition-all disabled:opacity-50"
                                    >
                                        <MessageSquare className="w-8 h-8 text-indigo-400" />
                                        <div className="text-center">
                                            <div className="font-semibold text-white">Chat</div>
                                            <div className="text-xs text-slate-400 mt-1">Ask questions</div>
                                        </div>
                                    </button>

                                    <button
                                        onClick={async () => {
                                            toggleFeature('clips')
                                            // Trigger clip extraction
                                            alert('Clip extraction will be implemented here')
                                        }}
                                        disabled={isProcessing}
                                        className="flex flex-col items-center space-y-3 p-6 bg-gradient-to-br from-rose-500/10 to-pink-500/10 border border-rose-500/20 rounded-xl hover:from-rose-500/20 hover:to-pink-500/20 transition-all disabled:opacity-50"
                                    >
                                        <Scissors className="w-8 h-8 text-rose-400" />
                                        <div className="text-center">
                                            <div className="font-semibold text-white">Extract Clips</div>
                                            <div className="text-xs text-slate-400 mt-1">Find key moments</div>
                                        </div>
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                            {/* Left Column: Controls */}
                            <div className="lg:col-span-4 space-y-6">

                                {/* Feature Selection */}
                                <div className="space-y-3">
                                    <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold px-1">Pipeline Features</h2>
                                    <FeatureToggles
                                        features={features}
                                        onToggle={toggleFeature}
                                        disabled={isProcessing}
                                    />
                                </div>

                                {/* Advanced Settings */}
                                <div className="space-y-3">
                                    <div className="flex items-center space-x-2 px-1">
                                        <Settings className="w-4 h-4 text-slate-500" />
                                        <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold">Advanced Options</h2>
                                    </div>
                                    <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-5 border border-slate-800/50 space-y-5">

                                        {/* Transcription Language */}
                                        <div className="space-y-2">
                                            <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">Transcription Language</label>
                                            <select
                                                value={settings.transcriptionLanguage}
                                                onChange={(e) => setSettings({ ...settings, transcriptionLanguage: e.target.value })}
                                                disabled={isProcessing}
                                                className="w-full bg-slate-950 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500/50 outline-none transition-all"
                                            >
                                                {Object.entries(appConfig.languages).map(([code, name]) => (
                                                    <option key={code} value={code}>{name}</option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Summary Language */}
                                        <div className="space-y-2">
                                            <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">Summary Language</label>
                                            <select
                                                value={settings.outputLanguage}
                                                onChange={(e) => setSettings({ ...settings, outputLanguage: e.target.value })}
                                                disabled={isProcessing}
                                                className="w-full bg-slate-950 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500/50 outline-none transition-all"
                                            >
                                                <option value="english">English</option>
                                                <option value="arabic">Arabic</option>
                                                <option value="original">Original Language</option>
                                            </select>
                                        </div>

                                        {/* AI Model */}
                                        <div className="space-y-2">
                                            <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">AI Model</label>
                                            <select
                                                value={settings.model}
                                                onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                                                disabled={isProcessing}
                                                className="w-full bg-slate-950 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500/50 outline-none transition-all"
                                            >
                                                {appConfig.models.map((model) => (
                                                    <option key={model} value={model}>{model}</option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Merge Clips */}
                                        <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                                            <label className="text-sm text-slate-300">Merge Clips into One Video</label>
                                            <input
                                                type="checkbox"
                                                checked={settings.mergeClips}
                                                onChange={(e) => setSettings({ ...settings, mergeClips: e.target.checked })}
                                                disabled={isProcessing}
                                                className="accent-primary-500 w-5 h-5 rounded"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Log Terminal */}
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center px-1">
                                        <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold">System Output</h2>
                                        {isProcessing && (
                                            <span className="text-xs text-primary-400 font-mono flex items-center space-x-2">
                                                <RefreshCw className="w-3 h-3 animate-spin" />
                                                <span>{status}... {progress}%</span>
                                            </span>
                                        )}
                                    </div>
                                    <LogTerminal logs={logs} className="h-[250px]" />
                                </div>
                            </div>

                            {/* Right Column: Upload & Results */}
                            <div className="lg:col-span-8 space-y-6">

                                {!results && (
                                    <div className="bg-slate-900/30 backdrop-blur-sm rounded-2xl p-6 border border-slate-800/50">
                                        <UploadSection
                                            onFileSelect={(file) => handleProcess(file, 'file')}
                                            onUrlSubmit={(url) => handleProcess(url, 'url')}
                                            isProcessing={isProcessing}
                                            hasLibrarySelection={!!selectedVideo?.transcript_text}
                                        />
                                    </div>
                                )}

                                {results && (
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h3 className="text-lg font-semibold text-white">Analysis Results</h3>
                                            <button
                                                onClick={handleClearSelection}
                                                className="flex items-center space-x-2 text-sm text-primary-400 hover:text-primary-300 transition-colors"
                                            >
                                                <RefreshCw className="w-4 h-4" />
                                                <span>Process New Video</span>
                                            </button>
                                        </div>
                                        <ResultsDashboard results={results} activeFeatures={features} />
                                    </div>
                                )}

                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}
