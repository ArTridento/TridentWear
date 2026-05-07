import { get, post } from "../shared/api.js?v=10";
import { initSite, showToast, withLoading, escapeHtml, getCurrentUser, pageUrl } from "../shared/site.js?v=10";

let threadsData = {};
let activeThreadId = null;

function scrollToBottom(container) {
  requestAnimationFrame(() => {
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  });
}

function renderSidebar() {
  const sidebar = document.getElementById("admin-chat-sidebar");
  const threadKeys = Object.keys(threadsData).sort((a, b) => {
    const lastA = threadsData[a][threadsData[a].length - 1];
    const lastB = threadsData[b][threadsData[b].length - 1];
    return new Date(lastB.timestamp) - new Date(lastA.timestamp);
  });

  if (threadKeys.length === 0) {
    sidebar.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--gray);">No messages yet.</div>`;
    return;
  }

  sidebar.innerHTML = threadKeys.map(tid => {
    const messages = threadsData[tid];
    const lastMsg = messages[messages.length - 1];
    const isUnread = lastMsg.role === "user" && !lastMsg.read;
    const timeString = new Date(lastMsg.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const author = lastMsg.author || "Guest";

    return `
      <div class="admin-chat-thread ${activeThreadId === tid ? 'is-active' : ''} ${isUnread ? 'is-unread' : ''}" data-thread="${escapeHtml(tid)}">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <div class="thread-name">${escapeHtml(author)}</div>
          <div class="thread-time">${timeString}</div>
        </div>
        <div class="thread-preview">${escapeHtml(lastMsg.message)}</div>
      </div>
    `;
  }).join("");

  sidebar.querySelectorAll(".admin-chat-thread").forEach(el => {
    el.addEventListener("click", () => {
      activeThreadId = el.dataset.thread;
      renderSidebar(); // update active class
      renderActiveChat();
    });
  });
}

function renderActiveChat() {
  const main = document.getElementById("admin-chat-main");
  if (!activeThreadId || !threadsData[activeThreadId]) {
    main.innerHTML = `
      <div class="empty-state" style="margin: auto; border: none;">
        <i class="fa-regular fa-comments empty-state-icon"></i>
        <span class="empty-copy">Select a conversation to view and reply.</span>
      </div>`;
    return;
  }

  const messages = threadsData[activeThreadId];
  const firstMsg = messages[0];

  main.innerHTML = `
    <div class="chat-header">
      <h2 class="chat-title" style="margin:0;">Chat with ${escapeHtml(firstMsg.author || "Guest")}</h2>
      <span style="margin-left:auto; font-size:0.8rem; color:var(--gray);">ID: ${escapeHtml(activeThreadId)}</span>
    </div>
    <div class="chat-messages" id="chat-messages">
      ${messages.map(msg => {
        const isAdmin = msg.role === "admin";
        const timeString = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return `
          <div class="chat-bubble-wrap ${isAdmin ? 'is-user' : 'is-admin'}">
            <div class="chat-bubble">${escapeHtml(msg.message)}</div>
            <span class="chat-time">${timeString}</span>
          </div>
        `;
      }).join("")}
    </div>
    <form class="chat-input-area" id="admin-chat-form">
      <input type="text" class="field" id="admin-chat-input" placeholder="Type a reply..." required autocomplete="off" />
      <button class="chat-send-btn" type="submit" aria-label="Send Reply">
        <i class="fa-solid fa-paper-plane"></i>
      </button>
    </form>
  `;

  const container = document.getElementById("chat-messages");
  scrollToBottom(container);

  const form = document.getElementById("admin-chat-form");
  const input = document.getElementById("admin-chat-input");
  const sendBtn = form.querySelector(".chat-send-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

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
        await post("/api/v1/admin/chat/reply", { thread_id: activeThreadId, message });
        
        const tempBubble = document.getElementById(tempId);
        if (tempBubble) tempBubble.remove();
        
        await loadThreads(); // Refresh to clear unread status and update lists
      } catch (err) {
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
        showToast("Failed to send reply.", "error");
      } finally {
        input.disabled = false;
        input.focus();
      }
    });
  });
}

async function loadThreads() {
  try {
    threadsData = await get("/api/v1/admin/chat");
    renderSidebar();
    if (activeThreadId) {
      renderActiveChat();
    }
  } catch (err) {
    console.error("Admin chat sync failed", err);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const user = getCurrentUser();
  if (!user || user.role !== "admin") {
    window.location.href = pageUrl(`/login?next=${encodeURIComponent("/admin/chat")}`);
    return;
  }

  await loadThreads();
  setInterval(loadThreads, 15000); // Poll for new messages every 15s
});
