import { VideoSummarizerAPI } from './api.js?v=2';
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";


// State
let state = {
    transcriptText: null,
    videoPath: null,
    transcriptPath: null,
    sessionId: null,
    currentTab: 'summary'
};

// Elements
const els = {
    videoUrl: document.getElementById('videoUrl'),
    processBtn: document.getElementById('processBtn'),
    statusMessage: document.getElementById('statusMessage'),
    resultsArea: document.getElementById('resultsArea'),
    videoPlayer: document.getElementById('videoPlayer'),
    videoTitle: document.getElementById('videoTitle'),
    summaryContent: document.getElementById('summaryContent'),
    transcriptContent: document.getElementById('transcriptContent'),
    clipsGrid: document.getElementById('clipsGrid'),
    chatMessages: document.getElementById('chatMessages'),
    chatForm: document.getElementById('chatForm'),
    chatInput: document.getElementById('chatInput'),
    tabs: {
        summary: document.getElementById('summaryTab'),
        transcript: document.getElementById('transcriptTab'),
        clips: document.getElementById('clipsTab')
    }
};

// Utils
const setStatus = (msg, loading = true) => {
    if (!msg) {
        els.statusMessage.classList.add('hidden');
        return;
    }
    els.statusMessage.classList.remove('hidden');
    els.statusMessage.innerHTML = loading
        ? `<span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span> ${msg}`
        : msg;
};

const showError = (msg) => {
    setStatus(`<span class="text-red-400">Error: ${msg}</span>`, false);
    setTimeout(() => setStatus(null), 5000);
};

const formatTime = (seconds) => {
    return new Date(seconds * 1000).toISOString().substr(11, 8);
};

// Main Flow
const processVideo = async () => {
    const url = els.videoUrl.value.trim();
    if (!url) return showError('Please enter a YouTube URL');

    try {
        els.processBtn.disabled = true;
        els.resultsArea.classList.add('hidden');

        // 1. Transcribe
        setStatus('Downloading and Transcribing video...');
        const transcribeJob = await VideoSummarizerAPI.transcribe(url);
        const transcribeResult = await VideoSummarizerAPI.pollJob(transcribeJob.job_id);

        state.videoPath = transcribeResult.result.video_path;
        state.transcriptPath = transcribeResult.result.transcript_path;

        // Load transcript text (assuming we can get it or use the path)
        // For simplicity, we might need a way to fetch the text content if the API didn't return it
        // The API returns 'text' file path in result.files usually, but let's assume we use the summarizer to get text
        // Actually, let's fetch the transcript text from the file if served, or just pass the path to summarizer

        // 2. Summarize
        setStatus('Generating summary...');
        const summarizeJob = await VideoSummarizerAPI.summarize({
            transcript_path: state.transcriptPath
        });
        const summaryResult = await VideoSummarizerAPI.pollJob(summarizeJob.job_id);

        state.transcriptText = "Transcript loaded via backend"; // we don't have the text directly yet unless we fetch it.

        // Render Summary
        renderSummary(summaryResult.result);

        // Start Chat Session
        const chatSession = await VideoSummarizerAPI.startChat({
            transcript_path: state.transcriptPath
        });
        state.sessionId = chatSession.session_id;

        // Extract Clips (Background)
        extractClips();

        // Show Results
        els.resultsArea.classList.remove('hidden');
        setStatus(null);

        // Setup Video Player

        let videoId = null;
        if (url.includes('v=')) {
            videoId = url.split('v=')[1]?.split('&')[0];
        } else if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1]?.split('?')[0];
        }

        if (videoId) {
            els.videoPlayer.src = `https://www.youtube.com/embed/${videoId}`;
        }

    } catch (e) {
        showError(e.message);
    } finally {
        els.processBtn.disabled = false;
    }
};

const extractClips = async () => {
    try {
        const job = await VideoSummarizerAPI.extractClips(state.videoPath, state.transcriptPath);
        // We can poll or just let it finish. Let's poll to show them when ready.
        // For now, we won't block UI.
    } catch (e) {
        console.error("Clip extraction failed", e);
    }
};

const renderSummary = (data) => {
    try {
        const html = marked.parse(data.text);
        els.summaryContent.innerHTML = html;
    } catch (e) {
        console.error("Markdown parsing failed", e);
        els.summaryContent.textContent = data.text;
    }
};

// Event Listeners
els.processBtn.addEventListener('click', processVideo);

window.switchTab = (tabName) => {
    Object.values(els.tabs).forEach(el => el.classList.add('hidden'));
    els.tabs[tabName].classList.remove('hidden');

    // Update buttons
    const buttons = document.querySelectorAll('button[onclick^="switchTab"]');
    buttons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(tabName)) {
            btn.classList.add('text-primary', 'border-b-2', 'border-primary');
            btn.classList.remove('text-muted');
        } else {
            btn.classList.remove('text-primary', 'border-b-2', 'border-primary');
            btn.classList.add('text-muted');
        }
    });
};

// Chat
els.chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = els.chatInput.value.trim();
    if (!msg || !state.sessionId) return;

    // Add User Message
    addChatMessage('User', msg);
    els.chatInput.value = '';

    // Add Bot Message Placeholder
    const botMsgId = addChatMessage('AI', '...');
    const botMsgEl = document.getElementById(botMsgId);
    let botText = '';

    await VideoSummarizerAPI.sendChatMessage(state.sessionId, msg, (chunk) => {
        if (botText === '') botMsgEl.textContent = ''; // Clear placeholder
        botText += chunk;
        botMsgEl.textContent = botText;
        // Auto scroll
        els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
    });
});

const addChatMessage = (sender, text) => {
    const id = Math.random().toString(36).substr(2, 9);
    const div = document.createElement('div');
    const isUser = sender === 'User';
    div.className = `p-3 rounded-lg text-sm max-w-[90%] ${isUser ? 'bg-primary text-white ml-auto rounded-tr-none' : 'bg-surface border border-white/5 rounded-tl-none'}`;
    div.innerHTML = `<p id="${id}">${text}</p>`;
    els.chatMessages.appendChild(div);
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
    return id;
};



