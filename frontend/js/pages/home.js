import { get } from "../shared/api.js";
import {
  bindProductCardActions,
  createSkeletonCards,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js";

async function loadFeaturedProducts() {
  const grid = document.querySelector("[data-featured-grid]");
  if (!grid) return;

  grid.innerHTML = createSkeletonCards(4);
  startProgress();

  try {
    const data = await get("/api/products?featured=true");
    const products = (Array.isArray(data) ? data : data.products || []).slice(0, 4);
    grid.innerHTML = products.map(productCardMarkup).join("");
    bindProductCardActions(grid, products);
  } catch (error) {
    grid.innerHTML = `<div class="helper-note danger">${error.message}</div>`;
  } finally {
    endProgress();
  }
}

async function loadStats() {
  const countEl = document.getElementById("customerCount");
  if (!countEl) return;
  
  let target = 50; // fallback
  try {
    const data = await get("/api/stats");
    if (data && typeof data.customers === 'number') {
      target = data.customers;
    }
  } catch (err) {
    // silently fallback to 50
  }

  const duration = 1000;
  const startTime = performance.now();
  
  function updateCount(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeOut = progress * (2 - progress);
    
    countEl.textContent = Math.floor(easeOut * target);
    
    if (progress < 1) {
      requestAnimationFrame(updateCount);
    } else {
      countEl.textContent = target;
    }
  }
  
  requestAnimationFrame(updateCount);
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  loadStats();
  await loadFeaturedProducts();
});
