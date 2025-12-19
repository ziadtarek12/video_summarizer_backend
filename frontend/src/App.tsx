
import { useState } from 'react'
import { VideoInput } from './components/VideoInput'
import { Dashboard } from './components/Dashboard'
import { Header } from './components/Header'

function App() {
    const [jobId, setJobId] = useState<string | null>(null)

    return (
        <div className="min-h-screen bg-background text-text selection:bg-primary selection:text-white">
            <Header />
            <main className="container mx-auto px-4 py-8 max-w-6xl">
                {!jobId ? (
                    <VideoInput onJobCreated={setJobId} />
                ) : (
                    <Dashboard jobId={jobId} onBack={() => setJobId(null)} />
                )}
            </main>
        </div>
    )
}

export default App
