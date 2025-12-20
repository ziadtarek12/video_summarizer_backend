import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn, Video, Sparkles, MessageSquare, Scissors } from 'lucide-react'
import { motion } from 'framer-motion'

export function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            await login(email, password)
            navigate('/')
        } catch (err) {
            setError('Invalid email or password')
        } finally {
            setLoading(false)
        }
    }

    const features = [
        { icon: Video, text: 'Upload videos or paste YouTube links' },
        { icon: Sparkles, text: 'AI-powered transcription & summaries' },
        { icon: MessageSquare, text: 'Chat about your video content' },
        { icon: Scissors, text: 'Extract key moments automatically' },
    ]

    return (
        <div className="min-h-screen animated-bg flex">
            {/* Left Side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
                {/* Background decorations */}
                <div className="absolute top-20 left-20 w-72 h-72 bg-primary-500/20 rounded-full blur-3xl" />
                <div className="absolute bottom-20 right-20 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="relative z-10 max-w-md"
                >
                    <div className="flex items-center space-x-4 mb-8">
                        <div className="p-4 bg-gradient-to-br from-primary-500/30 to-indigo-500/30 rounded-2xl border border-primary-500/20 glow-primary">
                            <Video className="w-10 h-10 text-primary-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold gradient-text">Video Summarizer AI</h1>
                            <p className="text-slate-400">Powered by Whisper & LLM</p>
                        </div>
                    </div>

                    <p className="text-xl text-slate-300 mb-10 leading-relaxed">
                        Transform your videos into actionable insights with AI-powered transcription, summarization, and intelligent chat.
                    </p>

                    <div className="space-y-4">
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
                                className="flex items-center space-x-4 p-4 bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/30"
                            >
                                <div className="p-2 bg-primary-500/10 rounded-lg">
                                    <feature.icon className="w-5 h-5 text-primary-400" />
                                </div>
                                <span className="text-slate-300">{feature.text}</span>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>

            {/* Right Side - Login Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-md"
                >
                    <div className="glass-card p-8 lg:p-10">
                        <div className="text-center mb-8">
                            <div className="inline-flex p-4 bg-gradient-to-br from-primary-500/20 to-indigo-500/20 rounded-2xl border border-primary-500/20 mb-4">
                                <LogIn className="w-8 h-8 text-primary-400" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
                            <p className="text-slate-400">Sign in to access your video library</p>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm text-center mb-6"
                            >
                                {error}
                            </motion.div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="input-field"
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Password</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input-field"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full btn-primary py-3.5 text-base font-semibold flex items-center justify-center space-x-2"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <LogIn className="w-5 h-5" />
                                        <span>Sign In</span>
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 pt-6 border-t border-slate-800">
                            <p className="text-center text-slate-400 text-sm">
                                Don't have an account?{' '}
                                <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
                                    Create one now
                                </Link>
                            </p>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
