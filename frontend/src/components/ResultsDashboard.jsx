import React, { useState } from 'react'
import clsx from 'clsx'
import { FileText, Sparkles, Scissors, MessageSquare, Copy, Check, Download, Clock, Star } from 'lucide-react'
import { ChatInterface } from './ChatInterface'

export function ResultsDashboard({ results, activeFeatures }) {
    const [activeTab, setActiveTab] = useState('transcript')
    const [copied, setCopied] = useState(false)

    // Show tabs based on both features AND available results
    const tabs = [
        { id: 'transcript', label: 'Transcript', icon: FileText, available: !!results?.transcript },
        { id: 'summary', label: 'Summary', icon: Sparkles, available: activeFeatures.summarize || !!results?.summary },
        { id: 'clips', label: 'Clips', icon: Scissors, available: activeFeatures.clips || !!results?.clips },
        { id: 'chat', label: 'AI Chat', icon: MessageSquare, available: activeFeatures.chat || !!results?.chatSessionId },
    ]

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const handleCopy = async (text) => {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="glass-card overflow-hidden flex flex-col h-[600px]">
            {/* Tabs */}
            <div className="flex border-b border-slate-800/50 bg-slate-950/50">
                {tabs.map((tab) => (
                    tab.available && (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={clsx(
                                "flex items-center space-x-2 px-6 py-4 font-medium transition-all relative",
                                activeTab === tab.id
                                    ? "text-white"
                                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/30"
                            )}
                        >
                            <tab.icon className={clsx(
                                "w-4 h-4 transition-colors",
                                activeTab === tab.id ? "text-primary-400" : "text-slate-500"
                            )} />
                            <span>{tab.label}</span>
                            {activeTab === tab.id && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-indigo-500" />
                            )}
                        </button>
                    )
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 p-6 overflow-y-auto">
                {activeTab === 'transcript' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center sticky top-0 bg-slate-900/90 backdrop-blur-sm py-2 -mt-2">
                            <h3 className="text-lg font-semibold text-white">Transcript</h3>
                            <div className="flex items-center space-x-2">
                                <button
                                    onClick={() => handleCopy(results?.transcript || '')}
                                    className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-slate-800/50 hover:bg-slate-700/50 rounded-lg transition-colors text-slate-300"
                                >
                                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                                </button>
                            </div>
                        </div>
                        <div className="bg-slate-800/30 rounded-xl p-5 border border-slate-700/30">
                            <pre className="whitespace-pre-wrap font-mono text-sm text-slate-300 leading-relaxed">
                                {results?.transcript || "No transcript available yet."}
                            </pre>
                        </div>
                    </div>
                )}

                {activeTab === 'summary' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-white">AI Summary</h3>
                            {results?.summary && (
                                <button
                                    onClick={() => handleCopy(results.summary.text || '')}
                                    className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-slate-800/50 hover:bg-slate-700/50 rounded-lg transition-colors text-slate-300"
                                >
                                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                                </button>
                            )}
                        </div>

                        {results?.summary ? (
                            <>
                                {/* Summary Text */}
                                <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-xl p-6">
                                    <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                                        {results.summary.text}
                                    </p>
                                </div>

                                {/* Key Points */}
                                {results.summary.key_points && results.summary.key_points.length > 0 && (
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Key Points</h4>
                                        <div className="space-y-2">
                                            {results.summary.key_points.map((point, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-start space-x-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30"
                                                >
                                                    <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                                        <span className="text-xs font-bold text-primary-400">{index + 1}</span>
                                                    </div>
                                                    <p className="text-slate-300 text-sm">{point}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="text-center py-12 text-slate-500">
                                <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-30" />
                                <p>Summary not generated yet.</p>
                                <p className="text-sm mt-1">Enable "Summarize" feature and process a video.</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'chat' && (
                    <ChatInterface transcript={results?.transcript} sessionId={results?.chatSessionId} />
                )}

                {activeTab === 'clips' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-white">Extracted Clips</h3>
                            {results?.clips?.extracted_files?.length > 0 && (
                                <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                                    {results.clips.extracted_files.length} files ready
                                </span>
                            )}
                        </div>

                        {results?.clips?.clips && results.clips.clips.length > 0 ? (
                            <div className="space-y-3">
                                {results.clips.clips.map((clip, index) => (
                                    <div
                                        key={index}
                                        className="bg-gradient-to-br from-rose-500/10 to-pink-500/10 border border-rose-500/20 rounded-xl p-4"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-white mb-1">{clip.title}</h4>
                                                <p className="text-sm text-slate-400 mb-3">{clip.description}</p>
                                                <div className="flex items-center space-x-4 text-xs text-slate-500">
                                                    <span className="flex items-center space-x-1">
                                                        <Clock className="w-3 h-3" />
                                                        <span>{formatTime(clip.start)} - {formatTime(clip.end)}</span>
                                                    </span>
                                                    <span className="flex items-center space-x-1">
                                                        <span>Duration: {formatTime(clip.duration)}</span>
                                                    </span>
                                                    <span className="flex items-center space-x-1">
                                                        <Star className="w-3 h-3 text-amber-400" />
                                                        <span>Importance: {clip.importance}/10</span>
                                                    </span>
                                                </div>
                                            </div>
                                            {/* Download button if file available */}
                                            {results?.clips?.extracted_files?.[index] && (
                                                <a
                                                    href={`/api/clips/download?path=${encodeURIComponent(results.clips.extracted_files[index])}`}
                                                    className="flex items-center space-x-1 px-3 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/30 transition-colors text-emerald-400 text-sm"
                                                    download
                                                >
                                                    <Download className="w-4 h-4" />
                                                    <span>Download</span>
                                                </a>
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {/* Download All Section */}
                                {results?.clips?.extracted_files?.length > 0 && (
                                    <div className="border-t border-slate-700/50 pt-4 mt-4">
                                        <h4 className="text-sm font-semibold text-slate-400 mb-3">Extracted Video Files</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {results.clips.extracted_files.map((filePath, idx) => (
                                                <a
                                                    key={idx}
                                                    href={`/api/clips/download?path=${encodeURIComponent(filePath)}`}
                                                    className="flex items-center space-x-2 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:bg-slate-700/50 transition-colors text-slate-300 text-sm"
                                                    download
                                                >
                                                    <Download className="w-4 h-4 text-emerald-400" />
                                                    <span>Clip {idx + 1}</span>
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {results.clips.message && (
                                    <p className="text-sm text-slate-500 text-center mt-4">{results.clips.message}</p>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-12 text-slate-500">
                                <Scissors className="w-12 h-12 mx-auto mb-4 opacity-30" />
                                <p>Clip extraction results will appear here.</p>
                                <p className="text-sm mt-1">Use "Extract Clips" to find key moments.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
