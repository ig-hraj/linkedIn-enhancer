/**
 * chat.js — AI Chatbot Functionality
 * 
 * Handles:
 *  - Sending/receiving chat messages
 *  - Conversation context management
 *  - Quick suggestion chips
 *  - Typing indicators
 *  - Chat history clearing
 */

// ============================================================
// Chat State
// ============================================================
let chatSessionId = generateSessionId();

// ============================================================
// DOM Ready — Initialize Chat
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("chat-send-btn");
    const chatInput = document.getElementById("chat-input");
    const clearBtn = document.getElementById("clear-chat-btn");

    // Send on button click
    sendBtn.addEventListener("click", sendMessage);

    // Send on Enter key (Shift+Enter for new line)
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea as user types
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + "px";
    });

    // Clear chat button
    clearBtn.addEventListener("click", clearChat);

    // Quick suggestion chips — clicking sends that message
    document.querySelectorAll(".suggestion-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            chatInput.value = chip.getAttribute("data-msg");
            sendMessage();
        });
    });
});

// ============================================================
// Send Message to Backend
// ============================================================
async function sendMessage() {
    const chatInput = document.getElementById("chat-input");
    const message = chatInput.value.trim();

    // Don't send empty messages
    if (!message) return;

    // Clear input field
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Display user message in the chat window
    addMessageToChat("user", message);

    // Show typing indicator while AI processes
    showTypingIndicator();

    // Disable send button to prevent double-sends
    const sendBtn = document.getElementById("chat-send-btn");
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                session_id: chatSessionId,
                profile_data: currentProfileData // Send profile for personalized advice
            })
        });

        const result = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (result.success) {
            // Display AI response
            addMessageToChat("bot", result.response);
            // Update session ID if server provided one
            if (result.session_id) {
                chatSessionId = result.session_id;
            }
        } else {
            addMessageToChat("bot", `⚠️ Error: ${result.error || "Something went wrong. Please try again."}`);
        }

    } catch (err) {
        removeTypingIndicator();
        console.error("Chat error:", err);
        addMessageToChat("bot", "⚠️ Could not connect to the server. Please make sure the backend is running.");
    }

    // Re-enable send button
    sendBtn.disabled = false;

    // Focus back on input
    chatInput.focus();
}

// ============================================================
// Add Message to Chat Display
// ============================================================
function addMessageToChat(role, content) {
    const messagesContainer = document.getElementById("chat-messages");

    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role}`;

    // Avatar icon
    const avatarIcon = role === "bot" ? "fa-robot" : "fa-user";

    // Format the content — convert markdown-like syntax to HTML
    const formattedContent = formatChatMessage(content);

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${avatarIcon}"></i>
        </div>
        <div class="message-content">
            ${formattedContent}
        </div>
    `;

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom to show latest message
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ============================================================
// Format Chat Message (Basic Markdown to HTML)
// ============================================================
function formatChatMessage(text) {
    // Escape HTML first to prevent XSS
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Bold: **text** → <strong>text</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Italic: *text* → <em>text</em>
    formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Numbered lists: lines starting with "1. ", "2. " etc.
    formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, "<li>$2</li>");

    // Bullet lists: lines starting with "- " or "• "
    formatted = formatted.replace(/^[-•]\s+(.+)$/gm, "<li>$1</li>");

    // Wrap consecutive <li> items in <ul>
    formatted = formatted.replace(/((<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

    // Line breaks: convert double newlines to paragraph breaks
    formatted = formatted.replace(/\n\n/g, "</p><p>");

    // Single newlines to <br>
    formatted = formatted.replace(/\n/g, "<br>");

    // Wrap in paragraph tags
    formatted = `<p>${formatted}</p>`;

    // Clean up empty paragraphs
    formatted = formatted.replace(/<p>\s*<\/p>/g, "");

    return formatted;
}

// ============================================================
// Typing Indicator
// ============================================================
function showTypingIndicator() {
    const messagesContainer = document.getElementById("chat-messages");

    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-message bot";
    typingDiv.id = "typing-indicator";
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) {
        indicator.remove();
    }
}

// ============================================================
// Clear Chat
// ============================================================
async function clearChat() {
    // Clear on server
    try {
        await fetch(`${API_BASE}/api/chat/clear`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: chatSessionId })
        });
    } catch (err) {
        console.log("Could not clear server-side chat:", err);
    }

    // Generate new session
    chatSessionId = generateSessionId();

    // Clear chat display — keep the welcome message
    const messagesContainer = document.getElementById("chat-messages");
    messagesContainer.innerHTML = `
        <div class="chat-message bot">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>👋 Chat cleared! I'm ready to help you optimize your LinkedIn profile.</p>
                <p>What would you like to work on?</p>
            </div>
        </div>
    `;

    showToast("🧹 Chat history cleared.");
}

// ============================================================
// Utility: Generate Session ID
// ============================================================
function generateSessionId() {
    return "session_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);
}
