/* ==========================================================
   Mutual Fund FAQ Assistant — UI Application Logic (app.js)
   Interacts with backend REST API to render conversation bubbles
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const messagesArea = document.getElementById("messages-area");
    const welcomeCard = document.getElementById("welcome-card");
    const sendBtn = document.getElementById("send-btn");

    // Endpoint URL - relative path allows hosting on the same FastAPI port
    const API_URL = "/api/chat";

    // ── 1. Event Listeners ──

    // Form Submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = chatInput.value.trim();
        if (query) {
            submitQuery(query);
        }
    });

    // Example Questions Click Handlers
    document.querySelectorAll(".example-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            if (query) {
                submitQuery(query);
            }
        });
    });

    // ── 2. Core Submission Function ──

    async function submitQuery(query) {
        // Clear input box
        chatInput.value = "";
        
        // Disable input during network call
        toggleInputState(false);

        // Hide welcome card upon first query
        if (welcomeCard) {
            welcomeCard.style.display = "none";
        }

        // 1. Render User Message
        appendMessageBubble(query, "user");
        scrollToBottom();

        // 2. Render Loading Indicator
        const loadingIndicator = appendLoadingIndicator();
        scrollToBottom();

        try {
            // 3. Dispatch API call
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query }),
            });

            // Remove loading indicator
            loadingIndicator.remove();

            if (!response.ok) {
                throw new Error(`API responded with status ${response.status}`);
            }

            const data = await response.json();

            // 4. Render Bot Response
            renderBotResponse(data);

        } catch (error) {
            if (loadingIndicator) loadingIndicator.remove();
            
            // Render error bubble on failure
            appendMessageBubble(
                "Sorry, I encountered a connection issue while communicating with the service. Please verify that the server is online and try again.",
                "bot",
                {
                    footer: "Connection Error",
                }
            );
        } finally {
            // Re-enable input boxes
            toggleInputState(true);
            scrollToBottom();
            chatInput.focus();
        }
    }

    // ── 3. Render Helper Functions ──

    function appendMessageBubble(text, sender, meta = {}) {
        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${sender}`;

        // Sanitize HTML slightly by escaping
        const escapedText = escapeHtml(text);

        let bubbleHtml = `<div class="bubble-content">${escapedText}</div>`;

        // Render meta elements if present
        if (sender === "bot" && (meta.citation || meta.educationalLink || meta.footer)) {
            let metaHtml = `<div class="bubble-meta">`;
            
            if (meta.citation) {
                metaHtml += `<a href="${meta.citation}" target="_blank" class="citation-link">🔗 Source Page</a>`;
            }
            if (meta.educationalLink) {
                metaHtml += `<a href="${meta.educationalLink}" target="_blank" class="refusal-link">📚 SEBI/AMFI Resource</a>`;
            }
            if (meta.footer) {
                metaHtml += `<span class="date-footer">${escapeHtml(meta.footer)}</span>`;
            }
            
            metaHtml += `</div>`;
            bubbleHtml += metaHtml;
        }

        bubble.innerHTML = bubbleHtml;
        messagesArea.appendChild(bubble);
        return bubble;
    }

    function renderBotResponse(data) {
        // Status can be success (factual) or refused (guardrails trigger)
        const answer = data.answer;
        const meta = {
            citation: data.citation,
            educationalLink: data.educational_link,
            footer: data.footer || "Facts-only. No investment advice.",
        };
        
        appendMessageBubble(answer, "bot", meta);
    }

    function appendLoadingIndicator() {
        const bubble = document.createElement("div");
        bubble.className = "loading-bubble";
        bubble.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        messagesArea.appendChild(bubble);
        return bubble;
    }

    // ── 4. Utility Functions ──

    function toggleInputState(enabled) {
        chatInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
        if (enabled) {
            sendBtn.style.opacity = "1";
            sendBtn.style.cursor = "pointer";
        } else {
            sendBtn.style.opacity = "0.6";
            sendBtn.style.cursor = "not-allowed";
        }
    }

    function scrollToBottom() {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    function escapeHtml(string) {
        return String(string)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
