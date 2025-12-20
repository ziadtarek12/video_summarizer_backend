import { useState } from 'react'
import { Video } from 'lucide-react'
import { useVideoProcessing } from './hooks/useVideoProcessing'
import { LogTerminal } from './components/LogTerminal'
import { FeatureToggles } from './components/FeatureToggles'
import { UploadSection } from './components/UploadSection'
import { ResultsDashboard } from './components/ResultsDashboard'

function App() {
    const {
        status,
        progress,
        logs,
        features,
        toggleFeature,
        processVideo,
        results
    } = useVideoProcessing()

    const isProcessing = status !== 'idle' && status !== 'completed' && status !== 'error'

    return (
        <div className="min-h-screen bg-slate-950 text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <header className="flex items-center space-x-4 pb-6 border-b border-slate-800">
                    <div className="p-3 bg-gradient-to-br from-primary-500/20 to-indigo-500/20 rounded-xl border border-primary-500/10">
                        <Video className="w-8 h-8 text-primary-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                            Video Summarizer AI
                        </h1>
                        <p className="text-slate-500 font-medium">Professional grade video transcription & analysis</p>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: Controls & Input (4 cols) */}
                    <div className="lg:col-span-4 space-y-6">

                        {/* 1. Feature Selection */}
                        <div className="space-y-3">
                            <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold px-1">Configuration</h2>
                            <FeatureToggles
                                features={features}
                                onToggle={toggleFeature}
                                disabled={isProcessing}
                            />
                        </div>

                        {/* 2. Log Terminal (visible during processing) */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center px-1">
                                <h2 className="text-sm uppercase tracking-wider text-slate-500 font-semibold">Live Logs</h2>
                                {isProcessing && (
                                    <span className="text-xs text-primary-400 font-mono animate-pulse">{status}... {progress}%</span>
                                )}
                            </div>
                            <LogTerminal logs={logs} className="h-[300px]" />
                        </div>
                    </div>

                    {/* Right Column: Main Action & Results (8 cols) */}
                    <div className="lg:col-span-8 space-y-6">

                        {/* Input Section */}
                        {!results && (
                            <div className="bg-slate-900/30 rounded-2xl p-6 border border-slate-800/50">
                                <UploadSection
                                    onFileSelect={(file) => processVideo(file, 'file')}
                                    onUrlSubmit={(url) => processVideo(url, 'url')}
                                    isProcessing={isProcessing}
                                />
                            </div>
                        )}

                        {/* Results Dashboard */}
                        {results && (
                            <ResultsDashboard results={results} activeFeatures={features} />
                        )}

                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
