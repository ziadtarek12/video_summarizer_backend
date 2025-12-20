import React, { useState, useRef } from 'react'
import { Upload, Link, Youtube, Play, CheckCircle } from 'lucide-react'
import clsx from 'clsx'
import { motion } from 'framer-motion'

export function UploadSection({ onFileSelect, onUrlSubmit, isProcessing, hasLibrarySelection }) {
    const [activeTab, setActiveTab] = useState('file')
    const [url, setUrl] = useState('')
    const [dragActive, setDragActive] = useState(false)
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        if (isProcessing) return

        const files = e.dataTransfer.files
        if (files && files.length > 0) {
            onFileSelect(files[0])
        }
    }

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            onFileSelect(e.target.files[0])
        }
    }

    // If library selection exists, show a different UI
    if (hasLibrarySelection) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
            >
                <div className="inline-flex p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 mb-4">
                    <CheckCircle className="w-10 h-10 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Video Ready for Processing</h3>
                <p className="text-slate-400 mb-6">
                    This video already has a transcript. You can summarize, chat, or extract clips without re-processing.
                </p>
                <p className="text-sm text-slate-500">
                    Select features from the left panel and view results in the tabs above.
                </p>
            </motion.div>
        )
    }

    return (
        <div className="space-y-5">
            {/* Tabs */}
            <div className="flex items-center space-x-1 p-1.5 bg-slate-900/50 rounded-xl border border-slate-800/50 w-fit">
                <button
                    onClick={() => setActiveTab('file')}
                    className={clsx(
                        "px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                        activeTab === 'file'
                            ? "bg-slate-800 text-white shadow-lg"
                            : "text-slate-400 hover:text-slate-200"
                    )}
                >
                    <div className="flex items-center space-x-2">
                        <Upload className="w-4 h-4" />
                        <span>Upload File</span>
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('url')}
                    className={clsx(
                        "px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                        activeTab === 'url'
                            ? "bg-slate-800 text-white shadow-lg"
                            : "text-slate-400 hover:text-slate-200"
                    )}
                >
                    <div className="flex items-center space-x-2">
                        <Youtube className="w-4 h-4" />
                        <span>YouTube URL</span>
                    </div>
                </button>
            </div>

            {/* Content */}
            <div className="relative">
                {activeTab === 'file' ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => !isProcessing && fileInputRef.current?.click()}
                        className={clsx(
                            "border-2 border-dashed rounded-2xl p-10 transition-all duration-300 flex flex-col items-center justify-center text-center space-y-5 group cursor-pointer",
                            isProcessing
                                ? "border-slate-800 bg-slate-900/30 opacity-50 cursor-not-allowed"
                                : dragActive
                                    ? "border-primary-500 bg-primary-500/10"
                                    : "border-slate-700/50 bg-slate-900/30 hover:border-primary-500/50 hover:bg-slate-800/30"
                        )}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            className="hidden"
                            accept="video/*,audio/*"
                        />
                        <div className={clsx(
                            "p-5 rounded-2xl transition-all duration-300",
                            isProcessing
                                ? "bg-slate-800"
                                : dragActive
                                    ? "bg-primary-500/20 scale-110"
                                    : "bg-slate-800/50 group-hover:bg-primary-500/10"
                        )}>
                            <Upload className={clsx(
                                "w-10 h-10 transition-all",
                                isProcessing
                                    ? "text-slate-600"
                                    : dragActive
                                        ? "text-primary-400"
                                        : "text-slate-400 group-hover:text-primary-400"
                            )} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-200 mb-1">
                                {isProcessing ? 'Processing in progress...' : 'Upload Video or Audio'}
                            </h3>
                            <p className="text-slate-500">
                                Drag & drop or click to browse
                            </p>
                            <p className="text-xs text-slate-600 mt-2">
                                Supports MP4, MOV, AVI, MP3, WAV and more
                            </p>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="bg-slate-900/30 border border-slate-700/50 rounded-2xl p-8 space-y-5"
                    >
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Link className="h-5 w-5 text-slate-500" />
                            </div>
                            <input
                                type="text"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://youtube.com/watch?v=..."
                                className="input-field pl-12"
                                disabled={isProcessing}
                            />
                        </div>
                        <button
                            onClick={() => onUrlSubmit(url)}
                            disabled={!url || isProcessing}
                            className="w-full btn-primary flex justify-center items-center py-3.5 space-x-2"
                        >
                            <Play className="w-5 h-5" />
                            <span className="font-semibold">Start Analysis</span>
                        </button>
                        <p className="text-xs text-center text-slate-500">
                            Paste a YouTube URL and we'll download, transcribe, and analyze it automatically
                        </p>
                    </motion.div>
                )}
            </div>
        </div>
    )
}
