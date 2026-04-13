import { get, getWithFallback } from "../shared/api.js";
import { initSite, showToast } from "../shared/site.js";

function getQueryId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

function updateProgress(statusStr) {
  const steps = document.querySelectorAll(".track-step");
  steps.forEach(s => s.classList.remove("active"));
  
  const s = (statusStr || "").toLowerCase();
  
  // Base logic
  if (s.includes("delivered")) {
    steps[0].classList.add("active");
    steps[1].classList.add("active");
    steps[2].classList.add("active");
    steps[3].classList.add("active");
  } else if (s.includes("out") || s.includes("transit")) {
    steps[0].classList.add("active");
    steps[1].classList.add("active");
    steps[2].classList.add("active");
  } else if (s.includes("ship")) {
    steps[0].classList.add("active");
    steps[1].classList.add("active");
  } else {
    // Default to placed
    steps[0].classList.add("active");
  }
}

async function doTrack(id) {
  const resDiv = document.getElementById("track-result");
  const btn = document.querySelector("[data-track-btn]");
  
  try {
    btn.disabled = true;
    btn.textContent = "Locating...";
    
    // In local dev, we might use mock API.
    const data = await get(`/api/orders/${id}/tracking`);
    
    document.getElementById("res-status").textContent = data.status || "Unknown";
    document.getElementById("res-courier").textContent = data.courier || "-";
    document.getElementById("res-tracking").textContent = data.tracking_id || "Unassigned";
    document.getElementById("res-est").textContent = data.estimated_delivery || "TBD";
    
    updateProgress(data.status);
    
    resDiv.style.display = "block";
  } catch (err) {
    resDiv.style.display = "none";
    showToast(err.message || "Order not found", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Track";
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();

  const form = document.querySelector("[data-track-form]");
  const input = document.getElementById("track-order-id");
  
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const id = input.value.trim();
    if(id) {
      window.history.pushState({}, "", `/track?id=${encodeURIComponent(id)}`);
      doTrack(id);
    }
  });

  const queryId = getQueryId();
  if (queryId) {
    input.value = queryId;
    doTrack(queryId);
  }
});
