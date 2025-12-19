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
    uploadBtn: document.getElementById('uploadBtn'),
    videoFileInput: document.getElementById('videoFileInput'),
    statusMessage: document.getElementById('statusMessage'),
    logsArea: document.getElementById('logsArea'),
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

const addLog = (msg) => {
    els.logsArea.classList.remove('hidden');
    const logEl = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();
    logEl.innerHTML = `<span class="text-white/40">[${timestamp}]</span> ${msg}`;
    els.logsArea.querySelector('div').appendChild(logEl);
    logEl.scrollIntoView({ behavior: 'smooth' });
};

const clearLogs = () => {
    els.logsArea.classList.add('hidden');
    els.logsArea.querySelector('div').innerHTML = '';
};

const showError = (msg) => {
    setStatus(`<span class="text-red-400">Error: ${msg}</span>`, false);
    addLog(`Error: ${msg}`);
};

const formatTime = (seconds) => {
    return new Date(seconds * 1000).toISOString().substr(11, 8);
};

const handleTranscriptionResult = async (transcribeJob) => {
    addLog("Transcription job started... polling for status.");
    const transcribeResult = await VideoSummarizerAPI.pollJob(transcribeJob.job_id, 2000, (step) => {
        setStatus(step);
        const lastLog = els.logsArea.querySelector('div').lastElementChild?.textContent;
        // Basic deduping to avoid spamming the log
        if (!lastLog || !lastLog.includes(step)) {
            addLog(step);
        }
    });
    addLog("Transcription completed successfully.");

    state.videoPath = transcribeResult.result.video_path;
    state.transcriptPath = transcribeResult.result.transcript_path;

    // 2. Summarize
    setStatus('Generating summary...');
    addLog("Generating summary...");
    const summarizeJob = await VideoSummarizerAPI.summarize({
        transcript_path: state.transcriptPath
    });
    const summaryResult = await VideoSummarizerAPI.pollJob(summarizeJob.job_id);
    addLog("Summary generated.");

    state.transcriptText = "Transcript loaded via backend";

    // Render Summary
    renderSummary(summaryResult.result);

    // Start Chat Session
    addLog("Starting chat session...");
    const chatSession = await VideoSummarizerAPI.startChat({
        transcript_path: state.transcriptPath
    });
    state.sessionId = chatSession.session_id;

    // Extract Clips (Background)
    addLog("Starting clip extraction (background)...");
    extractClips();

    // Show Results
    els.resultsArea.classList.remove('hidden');
    setStatus(null);
};
// Render functions
const renderSummary = (data) => {
    try {
        const html = marked.parse(data.text);
        els.summaryContent.innerHTML = html;
    } catch (e) {
        console.error("Markdown parsing failed", e);
        els.summaryContent.textContent = data.text;
    }

    // Key points (if available) - typically included in text or separately?
    // If backend returns keys points separately we can render them too.
};

// Main Flow
const processVideo = async () => {
    const url = els.videoUrl.value.trim();
    if (!url) return showError('Please enter a YouTube URL');

    try {
        els.processBtn.disabled = true;
        els.resultsArea.classList.add('hidden');
        clearLogs();

        // 1. Transcribe
        setStatus('Initializing...');
        addLog(`Initializing request for URL: ${url}`);
        const transcribeJob = await VideoSummarizerAPI.transcribe(url);

        if (transcribeJob.cached) {
            addLog("Found existing transcription for this video. Using cached results.");
        }

        await handleTranscriptionResult(transcribeJob);

        // Setup Video Player (YouTube)
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

const processFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        els.uploadBtn.disabled = true;
        els.resultsArea.classList.add('hidden');
        clearLogs();

        // 1. Upload and Transcribe
        setStatus('Uploading file...');
        addLog(`Uploading file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
        const transcribeJob = await VideoSummarizerAPI.transcribeFile(file);

        if (transcribeJob.cached) {
            addLog("Found existing transcription for this file. Using cached results.");
        }

        await handleTranscriptionResult(transcribeJob);

        // Setup Video Player (Local File - strict browser policies might prevent direct play from path)
        // Ideally we serve the file via static mount
        // For now, let's just show a placeholder or try to serve if possible
        els.videoPlayer.src = '';
        // We could mount the output dir and point to it: /output/{jobId}/{filename}

    } catch (e) {
        showError(e.message);
    } finally {
        els.uploadBtn.disabled = false;
        // Reset input
        els.videoFileInput.value = '';
    }
};

// Event Listeners
els.processBtn.addEventListener('click', processVideo);
els.uploadBtn.addEventListener('click', () => els.videoFileInput.click());
els.videoFileInput.addEventListener('change', processFile);

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



