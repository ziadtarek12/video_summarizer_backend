import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import { apiService } from '../services/api'

export function ChatInterface({ transcript }) {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Hello! I've analyzed the video. Ask me anything about it." }
    ])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [sessionId, setSessionId] = useState(null)

    const scrollRef = useRef(null)

    useEffect(() => {
        // Initialize session when component mounts
        const initSession = async () => {
            try {
                const res = await apiService.startChat(transcript)
                setSessionId(res.data.session_id)
            } catch (e) {
                setMessages(prev => [...prev, { role: 'assistant', content: "Error starting chat session. Please try again." }])
            }
        }
        if (transcript && !sessionId) {
            initSession()
        }
    }, [transcript, sessionId])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() || !sessionId || isLoading) return

        const userMessage = input.trim()
        setInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setIsLoading(true)

        try {
            // NOTE: For true streaming, we'd need to use fetch with ReadableStream reader here.
            // For this MVP, we will assume standard request or use a specific streaming helper.
            // Given the requirement for "better user experience", let's simulate streaming or implement it properly.

            const response = await fetch(`/api/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: userMessage
                })
            })

            if (!response.ok) throw new Error("Chat request failed")

            // Stream the response
            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let assistantMessage = ''

            setMessages(prev => [...prev, { role: 'assistant', content: '' }])

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                assistantMessage += chunk

                setMessages(prev => {
                    const newHistory = [...prev]
                    const lastMsg = newHistory[newHistory.length - 1]
                    if (lastMsg.role === 'assistant') {
                        lastMsg.content = assistantMessage
                    }
                    return newHistory
                })
            }

        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error answering that." }])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-full bg-slate-900">
            {/* Chat History */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-4"
            >
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={clsx(
                            "flex space-x-3 max-w-[85%]",
                            msg.role === 'user' ? "ml-auto flex-row-reverse space-x-reverse" : "mr-auto"
                        )}
                    >
                        <div className={clsx(
                            "p-2 rounded-full h-8 w-8 flex items-center justify-center flex-shrink-0",
                            msg.role === 'user' ? "bg-primary-500/20" : "bg-indigo-500/20"
                        )}>
                            {msg.role === 'user' ? <User className="w-4 h-4 text-primary-400" /> : <Bot className="w-4 h-4 text-indigo-400" />}
                        </div>

                        <div className={clsx(
                            "p-3 rounded-2xl text-sm leading-relaxed",
                            msg.role === 'user'
                                ? "bg-primary-600 text-white rounded-tr-none px-4"
                                : "bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700"
                        )}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex space-x-3 mr-auto items-center">
                        <div className="p-2 rounded-full h-8 w-8 flex items-center justify-center bg-indigo-500/20">
                            <Bot className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div className="px-3 py-2 bg-slate-800 rounded-2xl rounded-tl-none border border-slate-700">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-0"></div>
                                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-75"></div>
                                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-150"></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask anything about the video..."
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    )
}
