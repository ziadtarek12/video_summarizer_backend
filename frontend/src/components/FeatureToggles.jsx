import React from 'react'
import { Sparkles, MessageSquare, Scissors, FileText } from 'lucide-react'
import clsx from 'clsx'
import { motion } from 'framer-motion'

export function FeatureToggles({ features, onToggle, disabled }) {
    const items = [
        {
            id: 'transcribe',
            label: 'Transcribe',
            icon: FileText,
            color: 'bg-emerald-500',
            textColor: 'text-emerald-400',
            description: 'Convert speech to text',
            locked: true, // Always on
        },
        {
            id: 'summarize',
            label: 'Summarize',
            icon: Sparkles,
            color: 'bg-amber-500',
            textColor: 'text-amber-400',
            description: 'Generate AI summary',
        },
        {
            id: 'clips',
            label: 'Extract Clips',
            icon: Scissors,
            color: 'bg-rose-500',
            textColor: 'text-rose-400',
            description: 'Find key video moments',
        },
        {
            id: 'chat',
            label: 'AI Chat',
            icon: MessageSquare,
            color: 'bg-indigo-500',
            textColor: 'text-indigo-400',
            description: 'Ask questions about content',
        },
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {items.map((item) => {
                const isActive = features[item.id]
                const Icon = item.icon

                return (
                    <motion.div
                        key={item.id}
                        whileHover={!disabled && !item.locked ? { scale: 1.02 } : {}}
                        whileTap={!disabled && !item.locked ? { scale: 0.98 } : {}}
                        onClick={() => !disabled && !item.locked && onToggle(item.id)}
                        className={clsx(
                            "p-4 rounded-xl border transition-all duration-200 relative overflow-hidden cursor-pointer",
                            isActive
                                ? "bg-slate-800/80 border-slate-700 shadow-lg"
                                : "bg-slate-900 border-slate-800 opacity-60 grayscale-[0.5]",
                            disabled && "opacity-50 cursor-not-allowed",
                            item.locked && "cursor-default ring-1 ring-emerald-500/20"
                        )}
                    >
                        {isActive && (
                            <div className={clsx("absolute top-0 left-0 w-1 h-full", item.color)} />
                        )}

                        <div className="flex items-start space-x-4">
                            <div className={clsx(
                                "p-2 rounded-lg transition-colors",
                                isActive ? "bg-slate-700" : "bg-slate-800"
                            )}>
                                <Icon className={clsx("w-6 h-6", isActive ? item.textColor : "text-slate-400")} />
                            </div>
                            <div>
                                <div className="flex items-center space-x-2">
                                    <h3 className={clsx("font-medium", isActive ? "text-slate-100" : "text-slate-400")}>
                                        {item.label}
                                    </h3>
                                    {item.locked && (
                                        <span className="text-[10px] uppercase tracking-wider font-bold text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                                            Required
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-slate-500 mt-0.5">{item.description}</p>
                            </div>
                        </div>

                        {/* Switch UI */}
                        <div className="absolute top-4 right-4">
                            <div className={clsx(
                                "w-10 h-6 rounded-full transition-colors duration-300 relative",
                                isActive ? item.color.replace('bg-', 'bg-') : "bg-slate-700"
                            )}>
                                <div className={clsx(
                                    "absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform duration-300 shadow-sm",
                                    isActive ? "translate-x-4" : "translate-x-0"
                                )} />
                            </div>
                        </div>
                    </motion.div>
                )
            })}
        </div>
    )
}
