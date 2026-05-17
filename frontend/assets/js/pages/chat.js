import { get, post } from "../shared/api.js?v=20260430-v3";
import { initSite, showToast, withLoading, escapeHtml } from "../shared/site.js?v=20260430-v3";

let threadId = localStorage.getItem("tw_chat_thread_id") || "";

// State & Data Safety: Validate localStorage
if (threadId === "undefined" || threadId === "null" || typeof threadId !== "string") {
  threadId = "";
  localStorage.removeItem("tw_chat_thread_id");
}

function scrollToBottom(container) {
  requestAnimationFrame(() => {
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  });
}

function showTypingIndicator() {
  const container = document.getElementById("chat-messages");
  if (document.getElementById("typing-indicator")) return;
  
  container.insertAdjacentHTML("beforeend", `
    <div class="chat-bubble-wrap is-admin reveal-scale" id="typing-indicator">
      <div class="chat-bubble typing-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `);
  scrollToBottom(container);
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.remove();
}

function renderMessages(messages) {
  const container = document.getElementById("chat-messages");
  if (!messages || messages.length === 0) {
    if (!container.querySelector(".empty-state")) {
      container.innerHTML = `
        <div class="empty-state" style="margin: auto; border: none; opacity: 0.7;">
          <i class="fa-regular fa-comments empty-state-icon"></i>
          <span class="empty-copy">Start a conversation with our support team.</span>
        </div>`;
    }
    return;
  }

  const existingTyping = !!document.getElementById("typing-indicator");
  
  container.innerHTML = messages.map(msg => {
    const isUser = msg.role === "user";
    const timeString = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    return `
      <div class="chat-bubble-wrap ${isUser ? 'is-user' : 'is-admin'}">
        <div class="chat-bubble">${escapeHtml(msg.message)}</div>
        <span class="chat-time">${timeString}</span>
      </div>
    `;
  }).join("");

  if (existingTyping) showTypingIndicator();
  scrollToBottom(container);
}

async function loadMessages() {
  if (!threadId) return;
  try {
    const messages = await get(`/api/v1/chat/messages?thread_id=${encodeURIComponent(threadId)}`);
    renderMessages(messages);
  } catch (err) {
    console.error("Chat sync failed", err);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadMessages();

  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = form.querySelector(".chat-send-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    // Optimistic UI Append
    const container = document.getElementById("chat-messages");
    if (container.querySelector(".empty-state")) {
      container.innerHTML = "";
    }
    
    const tempId = "temp-" + Date.now();
    const timeString = "Sending...";
    container.insertAdjacentHTML("beforeend", `
      <div class="chat-bubble-wrap is-user" id="${tempId}" style="opacity: 0.6; transform: scale(0.98);">
        <div class="chat-bubble">${escapeHtml(message)}</div>
        <span class="chat-time">${timeString}</span>
      </div>
    `);
    scrollToBottom(container);
    input.value = "";
    input.disabled = true;

    await withLoading(sendBtn, async () => {
      try {
        const payload = { message, thread_id: threadId || null };
        const res = await post("/api/v1/chat/send", payload);
        
        if (res.thread_id && !threadId) {
          threadId = res.thread_id;
          localStorage.setItem("tw_chat_thread_id", threadId);
        }
        
        // Remove temp and load real
        const tempBubble = document.getElementById(tempId);
        if (tempBubble) tempBubble.remove();
        
        await loadMessages(); // Refresh to get server confirmed state
        showTypingIndicator(); // Show typing indicator to simulate support agent reading
        setTimeout(removeTypingIndicator, 3000); // Remove after 3s if no admin reply yet
        
      } catch (err) {
        // Error fallback
        const tempBubble = document.getElementById(tempId);
        if (tempBubble) {
          tempBubble.style.opacity = "1";
          tempBubble.querySelector(".chat-bubble").style.background = "var(--danger)";
          tempBubble.querySelector(".chat-time").innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Failed to send. Click to retry.`;
          tempBubble.style.cursor = "pointer";
          tempBubble.onclick = () => {
            input.value = message;
            tempBubble.remove();
            input.focus();
          };
        }
        showToast("Failed to send message.", "error");
      } finally {
        input.disabled = false;
        input.focus();
      }
    });
  });
  
  // Polling every 5 seconds
  setInterval(async () => {
    const oldLength = document.querySelectorAll(".chat-bubble-wrap").length;
    await loadMessages();
    const newLength = document.querySelectorAll(".chat-bubble-wrap").length;
    if (newLength > oldLength) removeTypingIndicator();
  }, 5000);
});
