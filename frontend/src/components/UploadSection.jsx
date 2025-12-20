import React, { useState, useRef } from 'react'
import { Upload, Link, Youtube } from 'lucide-react'
import clsx from 'clsx'

export function UploadSection({ onFileSelect, onUrlSubmit, isProcessing }) {
    const [activeTab, setActiveTab] = useState('file') // 'file' or 'url'
    const [url, setUrl] = useState('')
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => {
        e.preventDefault()
        e.stopPropagation()
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
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

    return (
        <div className="space-y-4">
            {/* Tabs */}
            <div className="flex items-center space-x-1 p-1 bg-slate-900 rounded-lg border border-slate-800 w-fit">
                <button
                    onClick={() => setActiveTab('file')}
                    className={clsx(
                        "px-4 py-2 rounded-md text-sm font-medium transition-all",
                        activeTab === 'file'
                            ? "bg-slate-800 text-white shadow-sm"
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
                        "px-4 py-2 rounded-md text-sm font-medium transition-all",
                        activeTab === 'url'
                            ? "bg-slate-800 text-white shadow-sm"
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
                    <div
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() => !isProcessing && fileInputRef.current?.click()}
                        className={clsx(
                            "border-2 border-dashed rounded-2xl p-8 transition-all duration-200 flex flex-col items-center justify-center text-center space-y-4 group",
                            isProcessing
                                ? "border-slate-800 bg-slate-900/50 opacity-50 cursor-not-allowed"
                                : "border-slate-700 bg-slate-900/50 hover:border-primary-500/50 hover:bg-slate-900/80 cursor-pointer"
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
                            "p-4 rounded-full transition-colors",
                            isProcessing ? "bg-slate-800" : "bg-slate-800 group-hover:bg-primary-500/20"
                        )}>
                            <Upload className={clsx(
                                "w-8 h-8 transition-colors",
                                isProcessing ? "text-slate-600" : "text-slate-400 group-hover:text-primary-400"
                            )} />
                        </div>
                        <div>
                            <h3 className="text-lg font-medium text-slate-200">
                                {isProcessing ? 'Processing in progress...' : 'Upload Video or Audio'}
                            </h3>
                            <p className="text-slate-500 mt-1">
                                Drag & drop or click to browse
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-8 space-y-4">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Link className="h-5 w-5 text-slate-500" />
                            </div>
                            <input
                                type="text"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://youtube.com/watch?v=..."
                                className="block w-full pl-10 pr-3 py-3 border border-slate-700 rounded-lg leading-5 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 sm:text-sm"
                                disabled={isProcessing}
                            />
                        </div>
                        <button
                            onClick={() => onUrlSubmit(url)}
                            disabled={!url || isProcessing}
                            className="w-full btn-primary flex justify-center items-center py-3"
                        >
                            Start Analysis
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
