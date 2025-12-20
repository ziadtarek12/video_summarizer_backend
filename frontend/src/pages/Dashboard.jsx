import { useState, useEffect } from 'react'
import { Video, LogOut, Layout, Settings, History } from 'lucide-react'
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
        reset
    } = useVideoProcessing()

    const [showLibrary, setShowLibrary] = useState(false)
    const [libraryVideos, setLibraryVideos] = useState([])
    const [settings, setSettings] = useState({
        outputLanguage: 'english',
        mergeClips: true,
        model: 'google/gemini-pro', // Default to a solid model
    })

    useEffect(() => {
        if (showLibrary) {
            loadLibrary()
        }
    }, [showLibrary])

    const loadLibrary = async () => {
        try {
            const res = await apiService.getLibrary()
            setLibraryVideos(res.data)
        } catch (e) {
            console.error("Failed to load library", e)
        }
    }

    const isProcessing = status !== 'idle' && status !== 'completed' && status !== 'error'

    const handleProcess = (input, type) => {
        // Pass settings to valid hooks if needed, or useVideoProcessing should accept them
        // For now we assume useVideoProcessing uses defaults or we modify it.
        // Actually, we should probably update useVideoProcessing to accept options.
        // But let's just pass them in processVideo for now.
        processVideo(input, type, settings)
    }

    return (
        <div className="min-h-screen bg-slate-950 text-white flex">

            {/* Sidebar (Library) */}
            <AnimatePresence>
                {showLibrary && (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 320, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="bg-slate-900 border-r border-slate-800 flex flex-col overflow-hidden"
                    >
                        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                            <h2 className="font-semibold text-slate-200">Your Library</h2>
                            <button onClick={() => setShowLibrary(false)} className="text-slate-500 hover:text-white">Close</button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {libraryVideos.map(vid => (
                                <div key={vid.id} className="p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 cursor-pointer transition-colors">
                                    <div className="text-sm font-medium truncate">{vid.title || vid.filename}</div>
                                    <div className="text-xs text-slate-500 mt-1">{new Date(vid.created_at).toLocaleDateString()}</div>
                                </div>
                            ))}
                            {libraryVideos.length === 0 && (
                                <div className="text-center text-slate-500 mt-10">No videos yet.</div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Header */}
                <header className="flex items-center justify-between px-8 py-4 border-b border-slate-800 bg-slate-950 z-10">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => setShowLibrary(!showLibrary)}
                            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                            title="Toggle Library"
                        >
                            <History className="w-5 h-5" />
                        </button>
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-gradient-to-br from-primary-500/20 to-indigo-500/20 rounded-lg border border-primary-500/10">
                                <Video className="w-6 h-6 text-primary-400" />
                            </div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                                Video Summarizer AI
                            </h1>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="text-sm text-slate-400">
                            Logged in as <span className="text-white font-medium">{user?.email}</span>
                        </div>
                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-rose-500/10 hover:text-rose-400 text-slate-400 transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="text-sm font-medium">Sign Out</span>
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-4 md:p-8 scrollbar-thin scrollbar-thumb-slate-800">
                    <div className="max-w-7xl mx-auto space-y-8">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                            {/* Left Column: Controls (4 cols) */}
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
                                    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 space-y-4">
                                        {/* Language */}
                                        <div className="space-y-2">
                                            <label className="text-xs text-slate-400 font-medium uppercase">Summary Language</label>
                                            <select
                                                value={settings.outputLanguage}
                                                onChange={(e) => setSettings({ ...settings, outputLanguage: e.target.value })}
                                                disabled={isProcessing}
                                                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 outline-none"
                                            >
                                                <option value="english">English (Default)</option>
                                                <option value="original">Original Video Language</option>
                                                <option value="spanish">Spanish</option>
                                                <option value="french">French</option>
                                            </select>
                                        </div>

                                        {/* Model */}
                                        <div className="space-y-2">
                                            <label className="text-xs text-slate-400 font-medium uppercase">AI Model</label>
                                            <select
                                                value={settings.model}
                                                onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                                                disabled={isProcessing}
                                                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 outline-none"
                                            >
                                                <option value="google/gemini-pro">Google Gemini Pro (Free)</option>
                                                <option value="mistralai/mistral-7b-instruct">Mistral 7B (OpenRouter Free)</option>
                                                <option value="openai/gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                                <option value="anthropic/claude-3-haiku">Claude 3 Haiku</option>
                                            </select>
                                        </div>

                                        {/* Clips */}
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm text-slate-300">Merge Clips into One Video</label>
                                            <input
                                                type="checkbox"
                                                checked={settings.mergeClips}
                                                onChange={(e) => setSettings({ ...settings, mergeClips: e.target.checked })}
                                                disabled={isProcessing}
                                                className="accent-primary-500 w-4 h-4"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Log Terminal */}
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center px-1">
                                        <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold">System Output</h2>
                                        {isProcessing && (
                                            <span className="text-xs text-primary-400 font-mono animate-pulse">{status}... {progress}%</span>
                                        )}
                                    </div>
                                    <LogTerminal logs={logs} className="h-[250px]" />
                                </div>
                            </div>

                            {/* Right Column: Actions & Results (8 cols) */}
                            <div className="lg:col-span-8 space-y-6">

                                {!results && (
                                    <div className="bg-slate-900/30 rounded-2xl p-6 border border-slate-800/50">
                                        <UploadSection
                                            onFileSelect={(file) => handleProcess(file, 'file')}
                                            onUrlSubmit={(url) => handleProcess(url, 'url')}
                                            isProcessing={isProcessing}
                                        />
                                    </div>
                                )}

                                {results && (
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h3 className="text-lg font-medium text-white">Analysis Results</h3>
                                            <button onClick={reset} className="text-sm text-primary-400 hover:text-primary-300">Process New Video</button>
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
