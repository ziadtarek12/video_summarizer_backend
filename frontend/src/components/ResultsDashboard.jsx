import React, { useState } from 'react'
import clsx from 'clsx'
import { FileText, Sparkles, Scissors, MessageSquare } from 'lucide-react'
import { ChatInterface } from './ChatInterface'

export function ResultsDashboard({ results, activeFeatures }) {
    const [activeTab, setActiveTab] = useState('transcript')

    const tabs = [
        { id: 'transcript', label: 'Transcript', icon: FileText },
        { id: 'summary', label: 'Summary', icon: Sparkles, disabled: !activeFeatures.summarize },
        { id: 'clips', label: 'Clips', icon: Scissors, disabled: !activeFeatures.clips },
        { id: 'chat', label: 'AI Chat', icon: MessageSquare, disabled: !activeFeatures.chat },
    ]

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-[600px]">
            {/* Tabs */}
            <div className="flex border-b border-slate-800 bg-slate-950">
                {tabs.map((tab) => (
                    !tab.disabled && (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={clsx(
                                "flex items-center space-x-2 px-6 py-4 font-medium transition-colors border-r border-slate-900",
                                activeTab === tab.id
                                    ? "bg-slate-900 text-white border-b-2 border-b-primary-500"
                                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-900/50"
                            )}
                        >
                            <tab.icon className={clsx("w-4 h-4", activeTab === tab.id ? "text-primary-400" : "text-slate-500")} />
                            <span>{tab.label}</span>
                        </button>
                    )
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 p-6 overflow-y-auto bg-slate-900">
                {activeTab === 'transcript' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-medium text-white sticky top-0 bg-slate-900 py-2">Transcript</h3>
                        <pre className="whitespace-pre-wrap font-mono text-sm text-slate-400 leading-relaxed">
                            {results?.transcript || "No transcript available yet."}
                        </pre>
                    </div>
                )}

                {activeTab === 'summary' && (
                    <div className="text-slate-400">
                        {/* Future: Render real summary here */}
                        Summary generation visualization coming soon.
                    </div>
                )}

                {activeTab === 'chat' && (
                    <ChatInterface transcript={results?.transcript} />
                )}

                {activeTab === 'clips' && (
                    <div className="text-slate-400">
                        {/* Future: Render clips grid here */}
                        Clip extraction results will appear here.
                    </div>
                )}
            </div>
        </div>
    )
}
