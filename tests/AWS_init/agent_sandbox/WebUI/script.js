const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const insightContent = document.getElementById('insight-content');

// WebSocket connection
let ws = null;

// Session ID for server
let sessionId = sessionStorage.getItem("sid") ?? crypto.randomUUID();
sessionStorage.setItem("sid", sessionId);

// Formatting for bold/italics
let currentAssistantMsg = null;
let currentAssistantRaw = "";

marked.setOptions({ breaks: true }); // single newlines become <br>

function renderMarkdown(el, raw) {
    el.innerHTML = DOMPurify.sanitize(marked.parse(raw));
}

function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);

    ws.onopen = () => {
        console.log('Connected to WebSocket');
        addInsightMessage("System", "Connected to server.", "block-status");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleStreamMessage(data);
        } catch (e) {
            console.error('Failed to parse message:', e);
        }
    };

    ws.onclose = () => {
        console.log('Disconnected from WebSocket');
        addInsightMessage("System", "Connection closed.", "block-status");
        // Attempt reconnect after 3 seconds if needed
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Think in BLOCKS not token by token
let currentThinkingBlock = null;

function handleStreamMessage(data) {
    switch (data.type) {
        case 'chunk':
            if (data.content_type === 'thinking') {
                if (!currentThinkingBlock) {
                    currentThinkingBlock = document.createElement('div');
                    currentThinkingBlock.className = 'insight-block block-thought';

                    const label = document.createElement('strong');
                    label.innerText = 'Thinking: ';
                    currentThinkingBlock.appendChild(label);

                    insightContent.appendChild(currentThinkingBlock);
                }
                currentThinkingBlock.appendChild(document.createTextNode(data.content));
            } else if (data.content_type === 'text') {
                currentThinkingBlock = null;

                if (!currentAssistantMsg) {
                    currentAssistantMsg = document.createElement('div');
                    currentAssistantMsg.className = 'message assistant';
                    chatHistory.appendChild(currentAssistantMsg);
                    currentAssistantRaw = "";
                }
                currentAssistantRaw += data.content;
                renderMarkdown(currentAssistantMsg, currentAssistantRaw);
            } else if (data.content_type === 'result') {
                const pre = document.createElement('pre');
                pre.className = 'tool-result';
                pre.innerText = data.content;
                chatHistory.appendChild(pre);

                currentAssistantMsg = null; // next text starts a new message
            }
            scrollToBottom();
            break;

        case 'status':
            currentThinkingBlock = null;
            addInsightMessage("Status", data.message, "block-status");
            break;

        case 'metrics':
            const metricsData = data.data;
            renderMetrics(metricsData);
            break;

        case 'error':
            alert(`Error: ${data.message}`);
            userInput.disabled = false;
            sendBtn.disabled = false;
            break;
            
        case 'end':
            currentAssistantMsg = null;
            currentThinkingBlock = null;
            addInsightMessage("System", "Stream complete.", "block-status");
            userInput.disabled = false;
            sendBtn.disabled = false;
            break;
    }
}

function renderMetrics(data) {
    const box = document.createElement('div');
    box.className = 'insight-block metrics-box';
    
    // Total Duration
    box.innerHTML += `<div class="metrics-item"><span>Total Duration:</span> <span>${(data.total_duration_s || 0).toFixed(3)}s</span></div>`;
    // Eval Count (Output Tokens)
    if (data.eval_count !== undefined) {
        box.innerHTML += `<div class="metrics-item"><span>Eval Count (Tokens):</span> <span>${data.eval_count}</span></div>`;
    }
    // Prompt Eval Count
    if (data.prompt_eval_count !== undefined) {
        box.innerHTML += `<div class="metrics-item"><span>Prompt Eval Count:</span> <span>${data.prompt_eval_count}</span></div>`;
    }
    // Done Reason
    if (data.done_reason) {
        box.innerHTML += `<div class="metrics-item"><span>Done Reason:</span> <span>${data.done_reason}</span></div>`;
    }

    insightContent.appendChild(box);
    scrollToBottom();
}

function addInsightMessage(title, text, cssClass) {
    const item = document.createElement('div');
    
    const container = document.createElement('div');
    container.className = `insight-block ${cssClass}`;
    
    // If it's a status message, we might want to show title separately or inline
    if (title) {
        const label = document.createElement('strong');
        label.innerText = title + ': ';
        container.appendChild(label);
        container.appendChild(document.createTextNode(text));
    } else {
        container.innerText = text;
    }

    insightContent.appendChild(container);
    scrollToBottom();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
    insightContent.scrollTop = insightContent.scrollHeight;
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) return;

    // Disable input while processing
    userInput.disabled = true;
    sendBtn.disabled = true;

    // Display User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user';
    userMsgDiv.innerText = message;
    chatHistory.appendChild(userMsgDiv);
    
    // Clear input
    userInput.value = '';
    scrollToBottom();

    // Send to WebSocket
    ws.send(JSON.stringify({
        session_id: sessionId,
        messages: [{ role: "user", content: message }]
    }));
}

async function newChat() {
    await fetch(`/api/reset?session_id=${sessionId}`, { method: "POST" });
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("sid", sessionId);

    chatHistory.innerHTML = "";
    insightContent.innerHTML = "";
    currentAssistantMsg = null;
    currentThinkingBlock = null;
}

document.getElementById('new-chat-btn').addEventListener('click', newChat);

// Initialize
connectWebSocket();
