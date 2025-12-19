
import { Film, LogOut } from 'lucide-react'
import { cn } from '../lib/utils'

export function Header() {
    return (
        <header className="border-b border-surface bg-background/50 backdrop-blur-md sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between max-w-6xl">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
                        <Film size={20} />
                    </div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        Video Summarizer
                    </h1>
                </div>
            </div>
        </header>
    )
}
