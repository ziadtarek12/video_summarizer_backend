
import { useState, useRef, useEffect } from 'react'
import { Send, User, Bot, Loader2 } from 'lucide-react'
import { startChat } from '../../services/api'
import { cn } from '../../lib/utils'

interface ChatViewProps {
    files: any
}

interface Message {
    role: 'user' | 'assistant'
    content: string
}

export function ChatView({ files }: ChatViewProps) {
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [streaming, setStreaming] = useState(false)
    const bottomRef = useRef<HTMLDivElement>(null)

    // Start session on mount
    useEffect(() => {
        const init = async () => {
            if (files.text) {
                try {
                    const res = await fetch(`/${files.text}`)
                    const text = await res.text()
                    const { session_id } = await startChat(text, "google")
                    setSessionId(session_id)
                    setMessages([{ role: 'assistant', content: "Hello! I've analyzed the video. Ask me anything about it!" }])
                } catch (e) {
                    console.error(e)
                }
            }
        }
        if (!sessionId) init()
    }, [files])

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, streaming])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || !sessionId || loading || streaming) return

        const userMsg = input
        setInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMsg }])
        setLoading(true)

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, message: userMsg })
            })

            if (!response.body) throw new Error("No response body")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            setMessages(prev => [...prev, { role: 'assistant', content: '' }])
            setLoading(false)
            setStreaming(true)

            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                const chunk = decoder.decode(value)
                setMessages(prev => {
                    const newHistory = [...prev]
                    const lastMsg = newHistory[newHistory.length - 1]
                    if (lastMsg.role === 'assistant') {
                        lastMsg.content += chunk
                    }
                    return newHistory
                })
            }
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
            setStreaming(false)
        }
    }

    return (
        <div className="flex flex-col h-[600px]">
            <div className="flex-1 overflow-y-auto space-y-4 pr-4 px-2">
                {messages.map((msg, i) => (
                    <div key={i} className={cn("flex gap-3", msg.role === 'user' ? "justify-end" : "justify-start")}>
                        {msg.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary flex-shrink-0 mt-1">
                                <Bot size={16} />
                            </div>
                        )}
                        <div className={cn(
                            "rounded-2xl px-4 py-2 max-w-[80%] text-sm md:text-base leading-relaxed",
                            msg.role === 'user'
                                ? "bg-primary text-white rounded-tr-none"
                                : "bg-surface border border-white/5 rounded-tl-none"
                        )}>
                            {msg.content}
                        </div>
                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white flex-shrink-0 mt-1">
                                <User size={16} />
                            </div>
                        )}
                    </div>
                ))}
                {(loading) && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary flex-shrink-0 mt-1">
                            <Bot size={16} />
                        </div>
                        <div className="bg-surface border border-white/5 rounded-2xl rounded-tl-none px-4 py-3">
                            <Loader2 className="animate-spin" size={16} />
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <form onSubmit={handleSubmit} className="mt-4 relative">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about the video..."
                    className="w-full bg-background border border-surface rounded-xl py-4 pl-4 pr-12 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                    disabled={!sessionId || loading || streaming}
                />
                <button
                    type="submit"
                    disabled={!input.trim() || !sessionId || loading || streaming}
                    className="absolute right-2 top-2 bottom-2 aspect-square bg-primary text-white rounded-lg flex items-center justify-center disabled:opacity-50 disabled:bg-surface disabled:text-muted transition-all hover:scale-95 active:scale-90"
                >
                    <Send size={18} />
                </button>
            </form>
        </div>
    )
}
