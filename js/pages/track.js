import { get } from "../shared/api.js";
import { initSite, startProgress, endProgress, showToast } from "../shared/site.js";

async function trackOrder() {
  const form = document.querySelector("[data-track-form]");
  const input = document.getElementById("track-order-id");
  const resultDiv = document.getElementById("track-result");
  
  if (!form || !input || !resultDiv) return;

  // Check URL for orderId
  const urlParams = new URLSearchParams(window.location.search);
  const orderId = urlParams.get("id");
  if (orderId) {
    input.value = orderId;
    triggerTracking(orderId);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = input.value.trim();
    if (id) triggerTracking(id);
  });
}

async function triggerTracking(orderId) {
  const resultDiv = document.getElementById("track-result");
  
  try {
    startProgress();
    const data = await get(`/api/orders/${orderId}/tracking`);
    
    resultDiv.style.display = "block";
    updateTrackingUI(data);
    
    // Smooth scroll to results
    resultDiv.scrollIntoView({ behavior: 'smooth' });
  } catch (error) {
    showToast(error.message || "Order not found", "error");
    resultDiv.style.display = "none";
  } finally {
    endProgress();
  }
}

function updateTrackingUI(data) {
  document.getElementById("res-status").textContent = data.status || "Pending";
  document.getElementById("res-courier").textContent = data.courier || "Standard Courier";
  document.getElementById("res-tracking").textContent = data.tracking_id || "Awaiting Shipment";
  document.getElementById("res-est").textContent = data.estimated_delivery || "TBD";

  // Update Progress Bar
  const steps = document.querySelectorAll(".track-step");
  steps.forEach(s => s.classList.remove("is-active", "is-complete"));

  const status = (data.status || "").toLowerCase();
  
  const mapping = {
    "confirmed": ["placed"],
    "processing": ["placed"],
    "shipped": ["placed", "shipped"],
    "in transit": ["placed", "shipped"],
    "out for delivery": ["placed", "shipped", "out"],
    "delivered": ["placed", "shipped", "out", "delivered"]
  };

  const activeSteps = mapping[status] || ["placed"];
  
  steps.forEach(step => {
    const slug = step.dataset.step;
    if (activeSteps.includes(slug)) {
      step.classList.add("is-complete");
      if (activeSteps[activeSteps.length - 1] === slug) {
        step.classList.add("is-active");
      }
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  trackOrder();
});
