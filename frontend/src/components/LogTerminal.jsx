import React, { useRef, useEffect } from 'react'
import { Terminal, XCircle, CheckCircle, Info, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { motion, AnimatePresence } from 'framer-motion'

export function LogTerminal({ logs, className }) {
    const scrollRef = useRef(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [logs])

    const getIcon = (type) => {
        switch (type) {
            case 'error': return <XCircle className="w-4 h-4 text-rose-500" />
            case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />
            case 'loading': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            default: return <Info className="w-4 h-4 text-slate-500" />
        }
    }

    return (
        <div className={clsx("bg-slate-950 rounded-xl border border-slate-800 overflow-hidden flex flex-col font-mono text-sm", className)}>
            <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-400 font-medium">System Output</span>
                </div>
                <div className="flex space-x-1.5">
                    <div className="w-3 h-3 rounded-full bg-slate-800"></div>
                    <div className="w-3 h-3 rounded-full bg-slate-800"></div>
                    <div className="w-3 h-3 rounded-full bg-slate-800"></div>
                </div>
            </div>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-2 max-h-[300px] scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
            >
                <AnimatePresence initial={false}>
                    {logs.length === 0 && (
                        <div className="text-slate-600 italic">Ready to process...</div>
                    )}
                    {logs.map((log, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-start space-x-3 text-slate-300"
                        >
                            <div className="mt-0.5 flex-shrink-0">
                                {getIcon(log.type)}
                            </div>
                            <div>
                                <span className="text-slate-500 text-xs mr-2">[{log.timestamp}]</span>
                                <span className={clsx(
                                    log.type === 'error' && 'text-rose-400',
                                    log.type === 'success' && 'text-emerald-400',
                                    log.type === 'loading' && 'text-blue-400'
                                )}>
                                    {log.message}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    )
}
